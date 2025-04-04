import json
import os
import chromadb
import glob
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_text_splitters import CharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_ollama import OllamaEmbeddings
from openai import OpenAI


def format_sse_message(message):
    data = {"value": message}
    sse_message = f"data: {json.dumps(data)}\n\n"
    return sse_message


def split_markdown_files(directory_path):
    folders = glob.glob(directory_path)
    text_loader_kwargs = {"encoding": "utf-8"}

    documents = []
    for folder in folders:
        doc_type = os.path.basename(folder)
        loader = DirectoryLoader(folder, glob="**/*.md", loader_cls=TextLoader, loader_kwargs=text_loader_kwargs)
        folder_docs = loader.load()
        for doc in folder_docs:
            doc.metadata["doc_type"] = doc_type
            documents.append(doc)

    text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=True)
    chunks = text_splitter.split_documents(documents)
    return chunks


def build_vector_database_for_markdown_files(client, directory_path, embedding_model, database_path, collection_name):
    chunks = split_markdown_files(directory_path)
    embeddings = OllamaEmbeddings(model=embedding_model)

    vectorstore = Chroma.from_documents(
        client=client,
        collection_name=collection_name,
        documents=chunks,
        embedding=embeddings,
        persist_directory=database_path)
    return vectorstore


class ChatUtil:
    __instance = None

    def __init__(self, stream_enabled):
        current_file_path = os.path.dirname(__file__)
        db_path = f'{current_file_path}/vector_db'
        self.__stream_enabled = stream_enabled
        self.__db_path = db_path
        self.__chroma_client = chromadb.PersistentClient(path=db_path)

        self.__chat_model = "deepseek-chat"
        self.__client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"), base_url="https://api.deepseek.com")
        self.__system_template = "请根据以下提供的上下文信息来回答最后的问题，请始终用中文回答。内容以Markdown的形式显示。"
        self.history = [{"role": "system", "content": self.__system_template}]

    @classmethod
    def get_instance(cls, stream_enabled):
        if not cls.__instance:
            cls.__instance = ChatUtil(stream_enabled)
            cls.__instance.__vector_store = cls.__instance.initialize_vector_store_for_markdown()
        cls.__instance.__stream_enabled = stream_enabled
        return cls.__instance

    def initialize_vector_store_for_markdown(self):
        collection_name = "markdown_collection"
        embedding_model = "nomic-embed-text"
        count = self.__chroma_client.count_collections()
        collections = self.__chroma_client.list_collections()
        if count > 0 and collection_name in collections:
            embeddings = OllamaEmbeddings(model=embedding_model)
            vectorstore = Chroma(client=self.__chroma_client, collection_name=collection_name,
                                 embedding_function=embeddings)
            return vectorstore
        else:
            current_file_path = os.path.dirname(__file__)
            source_document_folder = f'{current_file_path}/knowledge-base/*'
            """vectorstore = build_vector_database(self.__source_document_folder, self.__embedding_model_name,
                                                self.__db_path)"""
            vectorstore = build_vector_database_for_markdown_files(
                client=self.__chroma_client,
                directory_path=source_document_folder,
                embedding_model=embedding_model,
                database_path=self.__db_path,
                collection_name=collection_name)
            return vectorstore

    def retrieve_messages(self, user_message):
        content = ""
        if len(self.history) == 1:
            results = self.__vector_store.similarity_search(user_message, k=30)
            for res in results:
                print(f"Query data from vector db,content:\n{res.page_content},metadata:{res.metadata}")
                content += res.page_content + "\n"
        else:
            content = user_message

        self.history.append({"role": "user", "content": content})
        return self.history

    def chat_with_streaming(self, user_message):
        messages = self.retrieve_messages(user_message)
        response = self.__client.chat.completions.create(
            model=self.__chat_model,
            messages=messages,
            stream=True
        )

        reply = ""
        for chunk in response:
            if chunk.choices[0].delta and chunk.choices[0].delta.content:
                content = chunk.choices[0].delta.content
                sse_message = format_sse_message(content)
                reply += content
                yield sse_message

        print(f"回复的完整信息为:\n{reply}")
        self.history.append({"role": "user", "content": reply})
        print(f"The history number is:{len(self.history)}")

        finish_message = format_sse_message("Finish")
        yield finish_message

    def chat_with_no_stream(self, user_message):
        messages = self.retrieve_messages(user_message)
        response = self.__client.chat.completions.create(
            model=self.__chat_model,
            messages=messages,
            stream=False
        )

        result = response.choices[0].message.content.replace("```html", "").replace("```", "")
        self.history.append({"role": "user", "content": result})
        print(f"回复的信息为:{result}")
        return result

    def chat(self, user_message):
        return self.chat_with_streaming(
            user_message=user_message) if self.__stream_enabled else self.chat_with_no_stream(user_message=user_message)

    def clear_history(self):
        msg = f"共有{len(self.history) - 1}条历史记录被清除"
        self.history = self.history[:1]
        print(msg)
        return msg


__all__ = ['ChatUtil']
