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
		'region', 'comment', 'alternative_id1', 'alternative_id2']

def read_file(data_file):
	if data_file.type == "text/csv":
		df = pd.read_csv(data_file)
	elif data_file.type == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet":
		df = pd.read_excel(data_file, sheet_name=0)
	return (df)

@st.cache
def load_image(image_file):
	img = Image.open(image_file)
	return img 


def main():
	st.title("GP2 sample manifest checker")
	menu = ["For Fulgent", "For NIH (on plate)","For NIH (not on plate)","About"]
	choice = st.sidebar.selectbox("Menu",menu)
	if choice in menu[:2]:
		st.subheader("Opeartion:")
		data_file = st.sidebar.file_uploader("Upload Sample Manifest (CSV/XLSX)", type=['csv', 'xlsx'])
		if st.button("Check1"):
			if data_file is not None:
				file_details = {"Filename":data_file.name,"FileType":data_file.type,"FileSize":data_file.size}
				st.write(file_details)
				df = read_file(file_details)
				st.dataframe(df.head())
		
		if st.button("Check2"):
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
				st.error(f'{missing_cols} are missing. \nPlease use the template sheet')
			else:
				st.text(f'Column name OK')
				st.text(f'N of original data entries:{df.shape[0]}')
				x1 = df[pd.notna(df.sample_id)].copy()
				st.text(f'N of missing sample_id --> removed: {df.shape[0] - x1.shape[0]}')
				
				sample_id_dup =  x1.sample_id[x1.sample_id.duplicated()].unique()
				if len(sample_id_dup)>0:
					st.text(f'Duplicated sample_id:{sample_id_dup}')
					st.error(f'Unique sample IDs are required\n(clinical IDs can be duplicated if replicated)')
				
				if sum(pd.isna(x1.clinical_id))>0:
					st.text(f'N of entries with clinical ID missing:{sum(pd.isna(x1.clinical_id))}')
					st.error('All sample must have clinical ID (can be same as the sample ID)')
					
			
			  # study_arm and Phenotype
				nmiss_study_arm = sum(pd.isna(x1.study_arm))
				if nmiss_study_arm>0: # fill na
					st.text(f'N of study_arm info missing --> recoded as Unknown:{nmiss_study_arm}')
					x1['study_arm'] = x1.study_arm.fillna('Unknown')
				
				st.text('Counts by study_arm')
				st.text(x1.study_arm.value_counts())
				arms=x1.study_arm.unique()
				n_arms = st.columns(len(arms))
				phenotypes={}
				for i, x in enumerate(n_arms):
					with x:
						arm = arms[i]
						phenotypes[arm]=x.selectbox(f"Allocate phenotype for [{arm}]",['PD', 'Control', 'Prodromal', 'Other', 'Unknown'], key=i)
					st.text(phenotypes)


	# ncol = st.sidebar.number_input("Number of dynamic columns", 0, 20, 1)
	# cols = st.columns(ncol)



				# if nmiss_Phenotype>0: # fill na
				#	 print('N of Phenotype info missing --> recoded as "Not Reported":', nmiss_Phenotype)
				#	 x2['Phenotype']=x2.Phenotype.fillna("Not Reported")
				# # cross-tabulation of study_arm and Phenotype
				# print('\n=== study_arm X Phenotype ===')
				# xtab = x2.pivot_table(index='study_arm', columns='Phenotype', margins=True,
				#						 values='sample_id', aggfunc='count', fill_value=0)
				# print(xtab)
				# # undefined "Phenotype"
				# ph_er = np.setdiff1d(x2.Phenotype.astype('str'), ["PD", "Control", "Prodromal", "Other", "Not Reported"])
				# if len(ph_er)>0:
				#	 print(f'\nUndefined "Phenotype" value: {ph_er}')
				#	 flag=1


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

