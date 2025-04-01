import os
import chromadb
import glob
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_text_splitters import CharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_ollama import OllamaEmbeddings
from openai import OpenAI
import gradio as gr


class ChatUtil:
    __instance = None

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
        self.__system_template = "请根据以下提供的上下文信息来回答最后的问题，请始终用中文回答。请直接返回一段html。"
        self.history = [{"role": "system", "content": self.__system_template}]

    @classmethod
    def get_instance(cls):
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
            results = self.__vector_store.similarity_search(message, k=10)
            for res in results:
                print(f"Query data from vector db,content:{res.page_content},metadata:{res.metadata}")
                content += res.page_content + "\n"
        else:
            content = message

        self.history.append({"role": "user", "content": content})
        return self.history

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

    def new_topic(self):
        self.history = self.history[:1]
        print("对话上下文已经被清除")
        return "对话上下文已经被清除"


"""cu = ChatUtil.get_instance()
chatbot = gr.Interface(
    fn=cu.chat,
    inputs=gr.Textbox(label="用户输入"),
    outputs=gr.Textbox(label="机器人回复"),
    title="聊天机器人"
)
chatbot.launch(server_name="0.0.0.0", server_port=5000, inline=True)"""
__all__ = ['ChatUtil']
