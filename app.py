import streamlit as st
import streamlit.components.v1 as stc

# File Processing Pkgs
import pandas as pd
import numpy as np


cols = ['study', 'sample_id', 'sample_type',
		'DNA_volume', 'DNA_conc', 'r260_280',
		'Plate_name', 'Plate_position', 'clinical_id', 
		'study_arm', 'sex', 'race', 
		'age', 'age_of_onset', 'age_at_diagnosis', 'family_history',
		'region', 'comment', 'alternative_id1', 'alternative_id2', 
		'Phenotype','Genotyping_site', 'Sample_submitter', 'original_manifest']


@st.cache
def load_image(image_file):
	img = Image.open(image_file)
	return img 



def main():
	st.title("GP2 sample manifest checker")
	menu = ["For Fulgent", "For NIH (on plate)","For NIH (not on plate)","About"]
	choice = st.sidebar.selectbox("Menu",menu)

	if choice in menu[:2]:
		st.subheader("Dataset")
		data_file = st.file_uploader("Upload Sample Manifest (CSV/XLSX", type=['csv', 'xlsx'])
		if st.button("Check"):
			if data_file is not None:
				file_details = {"Filename":data_file.name,"FileType":data_file.type,"FileSize":data_file.size}
				st.write(file_details)
				if data_file.type == "text/csv":
					df = pd.read_csv(data_file)
				elif data_file.type == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet":
					df = pd.read_excel(data_file, sheet_name=0)

				st.dataframe(df.head())
			
			missing_cols = np.setdiff1d(cols, df.columns)
			if len(missing_cols)>0:
				st.info(f'{missing_cols} are missing. \nPlease use the template sheet')
			else:
				st.text(f'Column name OK')
				st.text(f'N of original data entries:{df.shape[0]}')
                x1 = df[pd.notna(df.sample_id)].copy()
                st.text(f'N of missing sample_id --> removed: {df.shape[0] - x1.shape[0]}')
                
                sample_id_dup =  x2.sample_id[x2.sample_id.duplicated()].unique()
                if len(sample_id_dup)>0:
                    st.text('Duplicated sample_id:', sample_id_dup)
				    st.info(f'Unique sample IDs are required\n(clinical IDs can be duplicated if replicated)')

	elif choice == menu[2]:
		st.subheader("Dataset")
		data_file = st.file_uploader("Upload Sample Manifest (CSV/XLSX", type=['csv', 'xlsx'])
		if st.button("Check"):
			if sm_file is not None:
				file_details = {"Filename":data_file.name,"FileType":data_file.type,"FileSize":data_file.size}
				st.write(file_details)
				df = pd.read_csv(data_file)
				st.dataframe(df)
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
				# 			page = pdf.pages[0]
				# 			st.write(page.extract_text())
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

