import json
import os
import chromadb
import glob
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_text_splitters import CharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_ollama import OllamaEmbeddings
from openai import OpenAI


def get_event_source_data(message):
    data = {"value":message}
    sse_message = f"data: {json.dumps(data)}\n\n"
    return sse_message


class ChatUtil:
    __instance = None
    __stream_instance = None

    def __init__(self):
        current_file_path = os.path.dirname(__file__)
        db_path = f'{current_file_path}/vector_db'
        self.__db_path = db_path
        self.__chroma_client = chromadb.PersistentClient(path=db_path)
        self.__collection_name = "langchain"
        self.__embedding_model_name = "nomic-embed-text"
        self.__source_document_folder = f'{current_file_path}/knowledge-base/*'
        self.__vector_store = self.load_vectordb()
        self.__chat_model = "deepseek-chat"
        self.__client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"), base_url="https://api.deepseek.com")
        self.__system_template = "请根据以下提供的上下文信息来回答最后的问题，请始终用中文回答。内容以Markdown的形式显示。"
        self.history = [{"role": "system", "content": self.__system_template}]

    @classmethod
    def get_instance(cls, stream=False):
        if stream:
            if cls.__stream_instance:
                return cls.__stream_instance
            else:
                cls.__stream_instance = ChatUtil()
                return cls.__stream_instance
        else:
            if cls.__instance:
                return cls.__instance
            else:
                cls.__instance = ChatUtil()
                return cls.__instance

    @classmethod
    def split_documents(cls, file_path):
        folders = glob.glob(file_path)
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

    def load_vectordb(self):
        count = self.__chroma_client.count_collections()

        if count > 0:
            embeddings = OllamaEmbeddings(model=self.__embedding_model_name)
            vectorstore = Chroma(client=self.__chroma_client, collection_name=self.__collection_name,
                                 embedding_function=embeddings)
            return vectorstore
        else:
            chunks = self.split_documents(self.__source_document_folder)
            embeddings = OllamaEmbeddings(model=self.__embedding_model_name)

            vectorstore = Chroma.from_documents(documents=chunks, embedding=embeddings,
                                                persist_directory=self.__db_path)
            return vectorstore

    def get_messages(self, message):
        content = ""
        if len(self.history) == 1:
            results = self.__vector_store.similarity_search(message, k=30)
            for res in results:
                print(f"Query data from vector db,content:\n{res.page_content},metadata:{res.metadata}")
                content += res.page_content + "\n"
        else:
            content = message

        self.history.append({"role": "user", "content": content})
        return self.history

    def chat_with_stream(self, message):
        messages = self.get_messages(message)
        response = self.__client.chat.completions.create(
            model=self.__chat_model,
            messages=messages,
            stream=True
        )

        reply = ""
        for chunk in response:
            if chunk.choices[0].delta and chunk.choices[0].delta.content:
                content = chunk.choices[0].delta.content
                sse_message = get_event_source_data(content)
                #print(sse_message)
                reply += content
                yield sse_message

        print(f"回复的完整信息为:\n{reply}")
        self.history.append({"role": "user", "content": reply})
        print(f"The history number is:{len(self.history)}")

        finish_message = get_event_source_data("Finish")
        yield finish_message

    def new_topic(self):
        self.history = self.history[:1]
        msg = f"共有{len(self.history)-1}条历史记录被清楚"
        print(msg)
        return msg

    def chat(self, message):
        messages = self.get_messages(message)
        response = self.__client.chat.completions.create(
            model=self.__chat_model,
            messages=messages,
            stream=False
        )

        result = response.choices[0].message.content.replace("```html", "").replace("```", "")
        self.history.append({"role": "user", "content": result})
        print(f"回复的信息为:{result}")
        return result


__all__ = ['ChatUtil']
