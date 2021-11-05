import streamlit as st
import streamlit.components.v1 as stc

# File Processing Pkgs
import pandas as pd


@st.cache
def load_image(image_file):
	img = Image.open(image_file)
	return img 



def main():
	st.title("File Upload Tutorial")

	menu = ["Dataset","Sample Manifest","About"]
	choice = st.sidebar.selectbox("Menu",menu)

	if choice == "Dataset":
		st.subheader("Dataset")
		data_file = st.file_uploader("Upload CSV",type=['csv'])
		if st.button("Process"):
			if data_file is not None:
				file_details = {"Filename":data_file.name,"FileType":data_file.type,"FileSize":data_file.size}
				st.write(file_details)
				df = pd.read_csv(data_file)
				st.dataframe(df)

	elif choice == "Sample Manifest":
		st.subheader("DocumentFiles")
		sm_file = st.file_uploader("Upload Sample Manifest File",type=['excel'])
		if st.button("Process"):
			if sm_file is not None:
				file_details = {"Filename":sm_file.name,"FileType":sm_file.type,"FileSize":sm_file.size}
				st.write(file_details)
				# # Check File Type
				# if sm_file.type == "text/plain":
				# 	# raw_text = sm_file.read() # read as bytes
				# 	# st.write(raw_text)
				# 	# st.text(raw_text) # fails
				# 	st.text(str(sm_file.read(),"utf-8")) # empty
				# 	raw_text = str(sm_file.read(),"utf-8") # works with st.text and st.write,used for futher processing
				# 	# st.text(raw_text) # Works
				# 	st.write(raw_text) # works
				# elif sm_file.type == "application/pdf":
				# 	# raw_text = read_pdf(sm_file)
				# 	# st.write(raw_text)
				# 	try:
				# 		with pdfplumber.open(sm_file) as pdf:
				# 		    page = pdf.pages[0]
				# 		    st.write(page.extract_text())
				# 	except:
				# 		st.write("None")
					    
					
				# elif sm_file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
				# # Use the right file processor ( Docx,Docx2Text,etc)
				# 	raw_text = docx2txt.process(sm_file) # Parse in the uploadFile Class directory
				# 	st.write(raw_text)

	else:
		st.subheader("About")
		st.info("Built with Streamlit")
		st.info("Hirotaka @DataTecnica")
		st.text("hirotaka-i")



if __name__ == '__main__':
	main()

