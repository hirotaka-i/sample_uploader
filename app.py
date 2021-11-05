import streamlit as st
import streamlit.components.v1 as stc

# File Processing Pkgs
import pandas as pd
import numpy as np

def checkSampleManifest(data, dup_not_allowed=True):
  """
  This function is to be used for data qc. 
  Input data should have columns named as the templete PLUS Phenotype!
  * Phenotype(["PD", "Control", "Prodromal", "Other", "Not Reported"])
  This checks the following
  1. columns
  2. unique sample_id (no mising)
  2. clincal_id can be duplicated but no missing
  3. Phenotype sex, race, sample_type should be given (no missing)
  4. For Fulgent samples, we need Plate_id and Plate_position
  """
  cols = ['study', 'sample_id', 'sample_type',
          'DNA_volume', 'DNA_conc', 'r260_280',
          'Plate_name', 'Plate_position', 'clinical_id', 
          'study_arm', 'sex', 'race', 
          'age', 'age_of_onset', 'age_at_diagnosis', 'family_history',
          'region', 'comment', 'alternative_id1', 'alternative_id2', 
          'Phenotype','Genotyping_site', 'Sample_submitter', 'original_manifest']
  nocols = np.setdiff1d(cols, data.columns)
  if len(nocols)>0:
    print('!!!SERIOUS ERROR!!! \nSome columns are missing')
    print('Missing columns:', nocols)
    return
  
  # start
  flag=0

  # NAs
  print('N of original data entries:', data.shape[0])
  x1 = data[pd.notna(data.sample_id)].copy()
  print('N of missing sample_id --> removed:', data.shape[0] - x1.shape[0])
  # duplication
  x2 = x1.drop_duplicates(keep='first').copy()
  print('N of duplicated entries --> removed:', x2.shape[0] - x1.shape[0])
  # effective entry
  print('\nN of effective entries:', x2.shape[0])
  # unique sample_id, clinical_id
  print('N of unique sample_id:', len(x2.sample_id.unique()))
  print('N of unique clinical_id:', len(x2.clinical_id.unique()), '\n')
  
  # dup check
  sample_id_dup =  x2.sample_id[x2.sample_id.duplicated()].unique()
  if len(sample_id_dup)>0:
    print('Duplicated sample_id:', sample_id_dup)
  clinical_id_dup =  x2.clinical_id[x2.clinical_id.duplicated()].unique()
  if len(clinical_id_dup)>0:
    print('Duplicated clinical_id:', clinical_id_dup)
  if (len(sample_id_dup) + len(clinical_id_dup)) > 0:
    if dup_not_allowed:
      print('If the duplications are fine, set option as dup_not_allowed=False')
      print('exit')
      return
    else: 
      print('"dup_not_allowed=False" option is active')
      print('!!DUPLICATIONS IGNORED!!')

  # All have clinical ID?
  if sum(pd.isna(x2.clinical_id))>0:
    print('\n!!!SERIOUS ERROR!!! \nPlease provide clinical ID for all entries with sample IDs')
    print('N of entries with clinical ID missing:', sum(pd.isna(x2.clinical_id)))
    return

  # study_arm and Phenotype
  nmiss_study_arm = sum(pd.isna(x2.study_arm))
  if nmiss_study_arm>0: # fill na
    print('N of study_arm info missing --> recoded as Unknown:', nmiss_study_arm)
    x2['study_arm'] = x2.study_arm.fillna('Unknown')
  nmiss_Phenotype = sum(pd.isna(x2.Phenotype))
  if nmiss_Phenotype>0: # fill na
    print('N of Phenotype info missing --> recoded as "Not Reported":', nmiss_Phenotype)
    x2['Phenotype']=x2.Phenotype.fillna("Not Reported")
  # cross-tabulation of study_arm and Phenotype
  print('\n=== study_arm X Phenotype ===')
  xtab = x2.pivot_table(index='study_arm', columns='Phenotype', margins=True,
                        values='sample_id', aggfunc='count', fill_value=0)
  print(xtab)
  # undefined "Phenotype"
  ph_er = np.setdiff1d(x2.Phenotype.astype('str'), ["PD", "Control", "Prodromal", "Other", "Not Reported"])
  if len(ph_er)>0:
    print(f'\nUndefined "Phenotype" value: {ph_er}')
    flag=1

  # sex
  nmiss_sex = sum(pd.isna(x2.sex))
  if nmiss_sex>0: # fill na
    print('\nsex info missing --> recoded as Unknown:', nmiss_sex)
    x2['sex'] = x2.sex.fillna('Unknown')
    flag=1
  else:
    print('\nsex info: no missing')
  sex_er = np.setdiff1d(x2.sex.unique().astype('str'), ["Male", "Female", "Intersex", "Unknown", "Other", "Not Reported"])
  if len(sex_er)>0:
    print('Undefined value:', sex_er)
    flag=1
  print(x2.sex.value_counts().to_frame())
  
  # race
  nmiss_race = sum(pd.isna(x2.race))
  if nmiss_race>0: # fill na
    print('\nrace info missing --> recoded as Unknown:', nmiss_race)
    x2['race'] = x2.race.fillna('Unknown')
    flag=1
  else:
    print('\nrace info: no missing')
  race_er = np.setdiff1d(x2.race.unique().astype('str'), ["American Indian or Alaska Native", "Asian", "White", "Black or African American", "Multi-racial", "Native Hawaiian or Other Pacific Islander", "Other", "Unknown", "Not Reported"])
  if len(race_er)>0:
    print('Undefined value:', race_er)
    flag=1
  print(x2.race.value_counts().to_frame())

@st.cache
def load_image(image_file):
	img = Image.open(image_file)
	return img 



def main():
	st.title("GP2 sample manifest checker")

	menu = ["For Fulgent","For NIH (on plate)","For NIH (not on plate)","About"]
	choice = st.sidebar.selectbox("Menu",menu)

	if choice == menu[0]:
		st.subheader(menu[0])
		data_file = st.file_uploader("Upload CSV",type=['csv'])
		if st.button("Process"):
			if data_file is not None:
				file_details = {"Filename":data_file.name,"FileType":data_file.type,"FileSize":data_file.size}
				st.write(file_details)
				df = pd.read_csv(data_file)
                df1 = checkSampleManifest(df)
                st.dataframe(df1)

	elif choice == menu[1]:
		st.subheader(menu[1])
		data_file = st.file_uploader("Upload xlsx",type=['xlsx'])
		if st.button("Process"):
			if data_file is not None:
				file_details = {"Filename":data_file.name,"FileType":data_file.type,"FileSize":data_file.size}
				st.write(file_details)
                df = pd.read_excel(data_file,sheet_name=0)
                st.dataframe(df)

				# # Check File Type
				# if data_file.type == "text/plain":
				# 	# raw_text = data_file.read() # read as bytes
				# 	# st.write(raw_text)
				# 	# st.text(raw_text) # fails
				# 	st.text(str(data_file.read(),"utf-8")) # empty
				# 	raw_text = str(data_file.read(),"utf-8") # works with st.text and st.write,used for futher processing
				# 	# st.text(raw_text) # Works
				# 	st.write(raw_text) # works
				# elif data_file.type == "application/pdf":
				# 	# raw_text = read_pdf(data_file)
				# 	# st.write(raw_text)
				# 	try:
				# 		with pdfplumber.open(data_file) as pdf:
				# 		    page = pdf.pages[0]
				# 		    st.write(page.extract_text())
				# 	except:
				# 		st.write("None")
					    
					
				# elif data_file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
				# # Use the right file processor ( Docx,Docx2Text,etc)
				# 	raw_text = docx2txt.process(data_file) # Parse in the uploadFile Class directory
				# 	st.write(raw_text)

	else:
		st.subheader("About")
		st.info("Built with Streamlit")
		st.info("Hirotaka @DataTecnica")
		st.text("hirotaka-i")



if __name__ == '__main__':
	main()

