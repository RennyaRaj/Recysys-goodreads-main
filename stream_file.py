import streamlit as st
import numpy as np
import pandas as pd

import sqlite3
conn=sqlite3.connect('data.db')
c=conn.cursor()

import os
import warnings
warnings.filterwarnings('ignore')

import tensorflow.keras as tf
import joblib

import base64
from io import BytesIO

ratings_1=pd.read_csv("ratings_1.csv")
ratings_2=pd.read_csv("ratings_2.csv")
ratings_3=pd.read_csv("ratings_3.csv")
ratings_4=pd.read_csv("ratings_4.csv")
ratings_5=pd.read_csv("ratings_5.csv")

ratings_df_list=[ratings_1,ratings_2,ratings_3,ratings_4,ratings_5]
ratings_df=pd.concat(ratings_df_list)

del ratings_1,ratings_2,ratings_3,ratings_4,ratings_5,ratings_df_list



new_model=tf.models.load_model("modelrecsys.h5")
co=joblib.load("contentsfile.joblib")
titlefile=joblib.load('title.joblib')


####To download dataframe recommondations
def to_excel(df):
    output = BytesIO()
    writer = pd.ExcelWriter(output, engine='xlsxwriter')
    df.to_excel(writer, sheet_name='Sheet1')
    writer.save()
    processed_data = output.getvalue()
    return processed_data

def get_table_download_link(df):
    #Generates a link allowing the data in a given panda dataframe to be downloaded
    #in:  dataframe
    #out: href string
    
    val = to_excel(df)
    b64 = base64.b64encode(val)  # val looks like b'...'
    return f'<a href="data:application/octet-stream;base64,{b64.decode()}" download="extract.xlsx">Download csv file</a>' # decode b'abc' => abc

##df = ... # your dataframe
##st.markdown(get_table_download_link(df), unsafe_allow_html=True)




def create_usertable():
  c.execute('CREATE TABLE IF NOT EXISTS userstable(username TEXT, password TEXT)')

def add_userdata(username,password):
  c.execute('INSERT INTO userstable(username, password) VALUES(?,?)',(username,password))
  conn.commit()

def login_user(username,password):
  c.execute('SELECT * FROM userstable WHERE username=? AND password=?',(username,password))
  data=c.fetchall()
  return data

def view_all_users():
  c.execute('SELECT * FROM userstable')
  data=c.fetchall()
  return data


st.title("...WELCOME...")
st.title("HYBRID BOOK RECOMMENDATION SYSTEM")
menu=["Home","Login", "Sign up","Book"]
choice=st.sidebar.selectbox("Menu",menu)

if choice=="Home":
  st.subheader("HOME")

elif choice=="Login":
  st.subheader("Login Section")
  
  username=st.sidebar.text_input("username")
  password=st.sidebar.text_input("password",type='password')
  
  if st.sidebar.checkbox("Login"):
    
    # if password=="12345":
    create_usertable()
    result=login_user(username,password)
    if result:

      st.success("LOGGED IN SUCCESSFULLY AS {} ".format(username))
      
      
      
      task=st.selectbox("Task",["Help","Start-Analytics","Profile"])
      
      if task=="Help":
        st.subheader("use Start-Analytics for Reccomondations")
      
      elif task=="Start-Analytics":

        st.subheader("Top N number of Book Recommondations predicted realtime")       

        
        #user_id = st.number_input('user_id',  min_value=1, max_value=53424, value=1)
        
        user_id=st.text_input("Enter user_id {1-53424} default 1")
        if user_id!="":
            user_id=int(user_id)
            if user_id<1 or user_id>53424:
                user_id=1                
                
        else:
            user_id=1

        us_id_temp=[user_id for i in range(len(co['book_id']))]
        reccom = new_model.predict([pd.Series(us_id_temp),co['book_id'],co.iloc[:,1:]])
        recc_df=pd.DataFrame(reccom,columns=["rating"])
        recc_df["book_id"]=co['book_id'].values
             

        df_new=ratings_df.where(ratings_df["user_id"]==user_id)
        df_new.dropna(inplace=True)
        list_books_seen=df_new['book_id'].tolist()
        del df_new

        recc_df_table = recc_df[~recc_df.book_id.isin(list_books_seen)]
        recc_df.sort_values(by="rating",ascending=False,inplace=True)   
        recc_df=recc_df.iloc[6:36].reset_index(drop=True)

        #num= st.number_input('required_reccomondation_count',  min_value=2, max_value=30, value=5)
        
        num=st.text_input("Enter required_reccomondation_count (2-30) default 2")
        
                    
        if num!="":
            num=int(num)
            if num<2 or num>30:
                num=2                
                
        else:
            num=2
        
        recc_df_table =recc_df.iloc[:num]
        recc_df_table=pd.merge(recc_df_table,titlefile,left_on="book_id",right_on="book_id")

        
        recc_df_table_new = recc_df_table.iloc[:,:6].reset_index(drop=True)
        
        st.write(recc_df_table_new)
        

        st.markdown(get_table_download_link(recc_df_table_new), unsafe_allow_html=True)
        for i in range(len(recc_df_table_new.index)):
          st.image( recc_df_table.iloc[i,7],
                width=200, # Manually Adjust the width of the image as per requirement
            caption=recc_df_table.iloc[i,4]
            )


        
      elif task=="Profile":
        st.subheader("User Profiles")
        user_result=view_all_users()
        clean_db=pd.DataFrame(user_result,columns=["Username","Password"])
        st.dataframe(clean_db)

    else:
      st.warning("Incorrect password/username")

elif choice=="Sign up":
  st.subheader("Create New Account")
  newuser=st.sidebar.text_input("username")
  newpassword=st.sidebar.text_input("password",type='password')

  if st.button("Sign up"):
    create_usertable()
    add_userdata(newuser,newpassword)
    st.success("You have successfully created a valid account")
    st.info("Goto Login menu")

elif choice=="Book":
  st.subheader("Enter Details...")
  userid=st.sidebar.text_input("userid")
  bookid=st.sidebar.text_input("bookid")
  st.button("SUBMIT")
