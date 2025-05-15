from langchain_community.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings  # New package
from langchain_community.document_loaders import TextLoader
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import CharacterTextSplitter

# Load documents
# loader = TextLoader("C:/Users/rrajm/Desktop/javanotes5.pdf")
loader = PyPDFLoader("C:/Raj/Movie/javanotes5.pdf")
documents = loader.load()

# Split documents
text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=0)
docs = text_splitter.split_documents(documents)

# Create embeddings
embedding_function = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

# Create vector store (auto-persists to directory)
vector_store = Chroma.from_documents(
    documents=docs,
    embedding=embedding_function,
    persist_directory="./chroma_db"
)

# Query similar documents
query = "what is class"
results = vector_store.similarity_search(query, k=3)

print("Start of search")

for doc in results:
    print(doc.page_content + "\n")

print("end of search")
print(f"Number of documents loaded: {vector_store.collection.count()}")