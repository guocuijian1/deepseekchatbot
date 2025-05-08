import os
import logging
import pandas as pd
from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings
from chromadb import PersistentClient
from langchain_text_splitters import CharacterTextSplitter
from langchain.schema import Document
from openai import OpenAI
from langchain.prompts import PromptTemplate

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

class OctaneService:
    instance = None

    def __init__(self, db_path):
        self.vectorstore = None
        self.db_path = db_path
        self.chroma_client = PersistentClient(path=db_path)
        self.collection_name = "octane_collection"
        self.chat_model = "deepseek-chat"
        self.embedding_model = "nomic-embed-text"
        self.context = ""
        self.excel_path = os.path.join(os.path.dirname(__file__), "knowledge-base/octane/backlog.xls")
        self.init_vector_db()

    @classmethod
    def get_instance(cls):
        if cls.instance is None:
            cls.instance = OctaneService(db_path="vector_db")
        return cls.instance

    def clear_history(self):
        self.context = ""
        logging.info("Chat history has been cleared.")
        return "Chat history has been cleared."

    def delete_collection(self):
        try:
            collections = self.chroma_client.list_collections()
            if self.collection_name in collections:
                self.chroma_client.delete_collection(self.collection_name)
                self.vectorstore = None
                logging.info(f"Collection '{self.collection_name}' has been deleted.")
                return f"Collection '{self.collection_name}' has been deleted."
            else:
                logging.warning(f"Collection '{self.collection_name}' does not exist.")
                return f"Collection '{self.collection_name}' does not exist."
        except Exception as e:
            logging.error(f"Error deleting collection: {e}")
            return f"Error deleting collection: {e}"

    def init_vector_db(self):
        try:
            collections = self.chroma_client.list_collections()
            if self.collection_name not in collections:
                self.embed_excel_to_vector_db()
            else:
                self.connect_to_existing_collection()
        except Exception as e:
            logging.error(f"Error initializing vector database: {e}")
            raise

    def connect_to_existing_collection(self):
        try:
            embeddings = OllamaEmbeddings(model=self.embedding_model)
            self.vectorstore = Chroma(
                client=self.chroma_client,
                collection_name=self.collection_name,
                embedding_function=embeddings
            )
            logging.info(f"Connected to existing collection: {self.collection_name}")
        except Exception as e:
            logging.error(f"Error connecting to collection: {e}")
            raise

    def get_excel_chunks(self):
        if not os.path.exists(self.excel_path):
            logging.error(f"Excel file not found: {self.excel_path}")
            raise FileNotFoundError(f"Excel file not found: {self.excel_path}")

        try:
            df = pd.read_excel(self.excel_path)
            documents = []

            for _, row in df.iterrows():
                page_content = ";".join([
                    f"{col}: {value if not pd.isna(value) else 'NULL'}"
                    for col, value in row.items()
                ])
                documents.append(Document(
                    page_content=page_content,
                    metadata={
                        "columns": str(row.index.tolist()),
                        "source": self.excel_path
                    }
                ))

            text_splitter = CharacterTextSplitter(
                chunk_size=1000,
                chunk_overlap=100,
                separator="\n",
                keep_separator=True
            )
            return text_splitter.split_documents(documents)
        except Exception as e:
            logging.error(f"Error processing Excel file: {e}")
            raise

    def embed_excel_to_vector_db(self):
        try:
            embeddings = OllamaEmbeddings(model=self.embedding_model)
            chunks = self.get_excel_chunks()

            self.vectorstore = Chroma.from_documents(
                client=self.chroma_client,
                collection_name=self.collection_name,
                documents=chunks,
                embedding=embeddings,
                persist_directory=self.db_path
            )
            logging.info(f"Data from {self.excel_path} has been embedded into the '{self.collection_name}' collection.")
        except Exception as e:
            logging.error(f"Error embedding data into vector database: {e}")
            raise

    def build_content(self, question, content):
        try:
            if not self.context and question:
                results = self.vectorstore.similarity_search(question, k=30)
                self.context = "\n".join([doc.page_content for doc in results])
                logging.info("Context built successfully.")
            elif content:
                self.context += content
            return self.context
        except Exception as e:
            logging.error(f"Error building content: {e}")
            raise

    def chat(self, message):
        try:
            prompt_template = PromptTemplate(
                input_variables=["context", "condition"],
                template="""Analyze the following records and return all entries where:

                            Context (semicolon-delimited key-value pairs):
                            {context}

                            **Instructions**:
                            1. Split records by "Owner Group:" (each record starts with this).
                            2. For each record:
                               - Parse key-value pairs by splitting at semicolons (`;`).
                               - Check if the record matches the condition Condition.
                            3. Return **full records** (all key-value pairs) that match, maintaining original formatting.

                            **Example Conditions**:
                            - "Name contains 'xxxx'"
                            - "Team = 'zzz' AND Phase = 'yyy'"
                            - "Story points > 3"

                            **Your Query**:
                            Condition = "{condition}"

                            **Expected Output**:
                            Owner Group: ...;ID: ...; [Full matching record(s)]"""
            )

            prompt = prompt_template.format(context=self.build_content(question=message, content=None), condition=message)
            llm = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"), base_url="https://api.deepseek.com")

            response = llm.chat.completions.create(
                model=self.chat_model,
                messages=[{"role": "user", "content": prompt}],
                stream=False
            )

            response_msg = response.choices[0].message.content.replace("```html", "").replace("```", "")
            self.build_content(question=None, content=response_msg)
            return response_msg
        except Exception as e:
            logging.error(f"Error during chat: {e}")
            raise

__all__ = ['OctaneService']