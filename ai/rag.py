import os
import numpy as np
import pandas as pd
import streamlit as st
import snowflake.connector
from huggingface_hub import InferenceClient
from dotenv import load_dotenv

load_dotenv()

EMBEDDING_MODEL = "BAAI/bge-small-en-v1.5"
CHAT_MODEL = "meta-llama/Llama-3.2-3B-Instruct"
NEW_REVIEWS = 500
TOP_K = 5
CACHE_FILE = "review_embedding.parquet"

client = InferenceClient(provider="auto", api_key=os.getenv("HF_ZOM"))

def get_private_key():
    from cryptography.hazmat.primitives import serialization
    with open(os.getenv("SNOWFLAKE_PRIVATE_KEY_PATH"), "rb") as key_file:
        p_key = serialization.load_pem_private_key(key_file.read(), password=None)
    return p_key.private_bytes(
        encoding=serialization.Encoding.DER,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )

def read_reviews_from_snowflake():
    conn = snowflake.connector.connect(
        user=os.getenv("SNOWFLAKE_USER"),
        account=os.getenv("SNOWFLAKE_ACCOUNT"),
        warehouse=os.getenv("SNOWFLAKE_WAREHOUSE"),
        database=os.getenv("SNOWFLAKE_DATABASE"),
        schema=os.getenv("SNOWFLAKE_SCHEMA"),
        private_key=get_private_key(),
    )
    query = f"""
        SELECT REVIEW_ID, CITY, RATING, COMMENT FROM ZOMATO.STAGING.STG_REVIEWS
        SAMPLE ({NEW_REVIEWS} ROWS)
    """
    df = conn.cursor().execute(query).fetch_pandas_all()
    conn.close()
    df.columns = [col.lower() for col in df.columns]
    return df

# def embed(texts):
#     # response = client.embeddings.create(model=EMBEDDING_MODEL,input=texts)
#     # print(response)
#     return [client.feature_extraction(t, model=EMBEDDING_MODEL) for t in texts]
#     # print(res)
    
from sentence_transformers import SentenceTransformer
embedder = SentenceTransformer(EMBEDDING_MODEL)  # "BAAI/bge-small-en-v1.5"

def embed(texts):
    return embedder.encode(texts, batch_size=32, show_progress_bar=True).tolist()
@st.cache_data()
def load_reviews():
    if os.path.exists(CACHE_FILE):
        return pd.read_parquet(CACHE_FILE)

    df = read_reviews_from_snowflake()
    df['embedding'] = embed(df['comment'].tolist())
    df.to_parquet(CACHE_FILE)
    return df


st.title("Chat with your Zomato reviews")
st.caption(f"Searching {NEW_REVIEWS} reviews, answering with {CHAT_MODEL}")

review_df = load_reviews()

question = st.text_input("ask a question about your reviews:",placeholder="e.g. what are the most common complaints about delivery?")



def find_similar_reviews(question, df):
    question_vector = embed([question])[0]
    scores = []
    for review_vector in df['embedding']:
        scores.append(cosine_similarity(question_vector,review_vector))

    df = df.copy()
    df["score"] = scores
    return df.nlargest(TOP_K,'score')
def cosine_similarity(vec_a, vec_b):
    return np.dot(vec_a, vec_b)/(np.linalg.norm(vec_a) * np.linalg.norm(vec_b))
def ask_llm(question, top_reviews):
    conext = ""

    for _, row in top_reviews.iterrows():
        conext += f" ({row['city']}, {row['rating']} stars) {row['comment']}\n"

    system_prompt = (
        "Answer ONLY using the customer reviews provided. "
        "Be concise. If the reviews don't covert it, say so"
    )

    user_prompt = f"Questions: {question}\n\nReviews:\n{conext}"

    response = client.chat.completions.create(
        model=CHAT_MODEL,
        temperature=0.2,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
    )
    return response.choices[0].message.content

if question:
    top_reviews = find_similar_reviews(question, review_df)
    answer = ask_llm(question, top_reviews)
    st.markdown(f"**Answer**")
    st.write(answer)

    with st.expander("Reviews used to build this answer"):
        st.dataframe(top_reviews[['city', 'rating', 'comment']], hide_index=True)   

