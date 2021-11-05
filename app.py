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
		st.subheader("Data Check and Phenotype Allocation")
		data_file = st.sidebar.file_uploader("Upload Sample Manifest (CSV/XLSX)", type=['csv', 'xlsx'])
		if data_file is not None:
			
			# for debug purpose. can be removed
			file_details = {"Filename":data_file.name,"FileType":data_file.type,"FileSize":data_file.size}
			st.write(file_details)
			
			# read a file
			df = read_file(data_file)
			df_non_miss_check = df[['study', 'sample_id', 'clinical_id', 'sex', 'study_arm']].copy()
			sample_id_dup =  df.sample_id[df.sample_id.duplicated()].unique()
			
			# missing check
			missing_cols = np.setdiff1d(cols, df.columns)
			if len(missing_cols)>0:
				st.error(f'{missing_cols} are missing. \nPlease use the template sheet')

			# required columns checks
			elif df_non_miss_check.isna().sum().sum()>0:
				st.error('There are some missing entries in the required columns.\nPlease fill the missing cells ')
				st.write(df_non_miss_check.info())

			# sample dup check
			elif len(sample_id_dup)>0:
				sample_id_dup =  df.sample_id[df.sample_id.duplicated()].unique()
				st.text(f'Duplicated sample_id:{sample_id_dup}')
				st.error(f'Unique sample IDs are required\n(clinical IDs can be duplicated if replicated)')
			else:
				st.text(f'Column name OK, required columns are non-missing, no duplicaiton for sample_id')
				st.text(f'N of sample_id (entries):{df.shape[0]}')
				st.text(f'N of unique clinical_id : {len(df.clinical_id.unique())}')

			# Sample Submitter
			Submitter = st.text_input('Sample Submitter (First name Initial + Last name) (e.g.- H. Morris)')
			df['Submitter'] = Submitter

			# study_arm --> Phenotype
			st.text('Counts by study_arm')
			st.text(df.study_arm.value_counts())
			arms=df.study_arm.dropna().unique()
			n_arms = st.columns(len(arms))
			phenotypes={}
			for i, x in enumerate(n_arms):
				with x:
					arm = arms[i]
					phenotypes[arm]=x.selectbox(f"Allocate phenotype for [{arm}]",["PD", "Control", "Prodromal", "Other", "Not Reported"], key=i)
			df['Phenotype'] = df.study_arm.map(phenotypes)

			# race standardization
			st.text('Counts by race')
			st.text(df.race.value_counts(dropna=False))
			races = df.race.dropna().unique()
			nmiss = sum(pd.isna(df.race))
			if nmiss>0:
				st.text(f'{nmiss} missing entries are recoded as "Not Reported"')
				df['race_for_qc'] = df.race.fillna('Not Reported')
			
			mapdic = {'Not Reported':'Not Reported'}
			for race in races:
				mapdic[race]=st.selectbox(f"[{race}]: For QC purppose, select the best match from the followings",
				["American Indian or Alaska Native", "Asian", "White", "Black or African American", 
				"Multi-racial", "Native Hawaiian or Other Pacific Islander", "Other", "Unknown"])
			df['race_for_qc'] = df.race_for_qc.map(mapdic)

			if st.button("Confirm Phenotype Allocation"):
				# cross-tabulation of study_arm and Phenotype
				st.text('=== Phenotype x study_arm===')
				xtab = df.pivot_table(index='Phenotype', columns='study_arm', margins=True,
										values='sample_id', aggfunc='count', fill_value=0)
				st.text(xtab)

			if st.button("Confirm Race for QC"):
				# cross-tabulation of study_arm and Phenotype
				st.text('=== race_for_qc X race ===')
				df['race'] = df.race.fillna('Missing')
				xtab = df.pivot_table(index='race_for_qc', columns='race', margins=True,
										values='sample_id', aggfunc='count', fill_value=0)
				st.text(xtab)

			if st.button("Plate check"):
				st.info('Please make sure, N of samples on each plate are =<96')
				df['Plate_name'] = df.Plate_name.fillna('Missing')
				for plate in df.Plate_name.unique():
					df_plate = df[df.Plate_name==plate].copy()
					df_plate_pos = df_plate.Plate_position
					# duplicated position check
					if plate!='Missing':
						dup_pos = df_plate_pos[df_plate_pos.duplicated()].unique()
						if len(dup_pos)>0:
							st.error(f'\n!!!SERIOUS ERROR!!! \nPlate position duplicated\nposition {dup_pos} on plate [{plate}]')
						
				xtab = df.pivot_table(index='Plate_name', 
									columns='study_arm', margins=True,
									values='sample_id', aggfunc='count', fill_value=0)
				st.write(xtab)
			
			if st.button('Age distribution check'):
				st.text('building')
			
			
			if st.button("Check2"):
				st.write(df.head())


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

