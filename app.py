import streamlit as st
import streamlit.components.v1 as stc

# File Processing Pkgs
import pandas as pd
import numpy as np
import base64
import datetime as dt
# import matplotlib.pyplot as plt # don't work...
today = dt.datetime.today()
version = f'{today.year}{today.month}{today.day}'



def read_file(data_file):
	if data_file.type == "text/csv":
		df = pd.read_csv(data_file)
	elif data_file.type == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet":
		df = pd.read_excel(data_file, sheet_name=0)
	return (df)

def get_table_download_link(df):
	"""Generates a link allowing the data in a given panda dataframe to be downloaded
	in:  dataframe
	out: href string
	"""
	csv = df.to_csv(index=False)
	study_code = df.study.unique()[0]
	b64 = base64.b64encode(csv.encode()).decode()  # some strings <-> bytes conversions necessary here
	href = f'<a href="data:file/csv;base64,{b64}"  download="{study_code}_sample_manifest_selfQC_{version}.csv">Download csv file</a>'
	return href
	
# @st.cache
# def load_image(image_file):
# 	img = Image.open(image_file)
# 	return img 


def main():
	menu = ["For Fulgent", "For NIH (on plate)","For NIH (not on plate)","About"]
	choice = st.sidebar.selectbox("Menu",menu)
	flag=0
	ph_conf=0
	sex_conf=0
	race_conf=0
	fh_conf=0
	cols = ['study', 'sample_id', 'sample_type',
		'DNA_volume', 'DNA_conc', 'r260_280',
		'Plate_name', 'Plate_position', 'clinical_id', 
		'study_arm', 'sex', 'race', 
		'age', 'age_of_onset', 'age_at_diagnosis', 'family_history',
		'region', 'comment', 'alternative_id1', 'alternative_id2']
	required_cols = ['study', 'sample_id', 'sample_type', 'clinical_id','study_arm', 'sex']
	fulgent_cols = ['DNA_volume', 'DNA_conc', 'Plate_name', 'Plate_position']
	data_file = st.sidebar.file_uploader("Upload Sample Manifest (CSV/XLSX)", type=['csv', 'xlsx'])
	

	st.title("GP2 sample manifest checker")
	st.text('This is a web app to self-check the sample manifest')
	st.text('The template download from the below link')
	st.write('https://docs.google.com/spreadsheets/d/1ThpUVBCRaPdDSiQiKZVwFpwWbW8mZxhqurv7-jBPrM4')
	st.text('In the above link, go to "File"> "Download" (as xlsx/csv) ')
	if data_file is not None:
		st.header("Data Check and self-QC")
		# for debug purpose. get the file detail
		# file_details = {"Filename":data_file.name,"FileType":data_file.type,"FileSize":data_file.size}
		# st.write(file_details)
		
		# read a file
		df = read_file(data_file)
		if choice=='For Fulgent':
			required_cols = required_cols + fulgent_cols
			st.text(f'Required for Fulgent: {fulgent_cols}')
		df_non_miss_check = df[required_cols].copy()
		sample_id_dup = df.sample_id[df.sample_id.duplicated()].unique()
		
		# missing check
		missing_cols = np.setdiff1d(cols, df.columns)
		if len(missing_cols)>0:
			st.error(f'{missing_cols} are missing. Please use the template sheet')
			flag=1
		
		# required columns checks
		elif df_non_miss_check.isna().sum().sum()>0:
			st.error('There are some missing entries in the required columns. Please fill the missing cells ')
			st.text('First ~30 columns with missing data in any required fields')
			st.write(df_non_miss_check[df_non_miss_check.isna().sum(1)>0].head(20))
			flag=1
		
		# sample dup check
		elif len(sample_id_dup)>0:
			sample_id_dup = df.sample_id[df.sample_id.duplicated()].unique()
			st.text(f'Duplicated sample_id:{sample_id_dup}')
			st.error(f'Unique sample IDs are required (clinical IDs can be duplicated if replicated)')
			flag=1
		else:
			st.text(f'Column name OK, required columns are non-missing, no duplicaiton for sample_id')
			st.text(f'N of sample_id (entries):{df.shape[0]}')
			st.text(f'N of unique clinical_id : {len(df.clinical_id.unique())}')

		# study_arm --> Phenotype
		st.subheader('Create "Phenotype"')
		st.text(df.study_arm.value_counts())
		arms=df.study_arm.dropna().unique().astype('str')
		n_arms = st.columns(len(arms))
		phenotypes={}
		for i, x in enumerate(n_arms):
			with x:
				arm = arms[i]
				phenotypes[arm]=x.selectbox(f"[{arm}]: For QC, please pick the Phenotype below",["PD", "Control", "Prodromal", "Other", "Not Reported"], key=i)
		df['Phenotype'] = df.study_arm.astype('str').map(phenotypes)

		# cross-tabulation of study_arm and Phenotype
		st.text('=== Phenotype x study_arm===')
		xtab = df.pivot_table(index='Phenotype', columns='study_arm', margins=True,
								values='sample_id', aggfunc='count', fill_value=0)
		st.text(xtab)
		if st.button("Confirm?"):
			st.info('Thank you!')
			ph_conf=1

		# race for qc
		st.subheader('Create "race_for_qc"')
		st.text(df.race.value_counts())
		races = df.race.dropna().unique().astype('str')
		nmiss = sum(pd.isna(df.race))
		if nmiss>0:
			st.text(f'{nmiss} entries missing race...')
			df['race_for_qc'] = df.race.astype('str').fillna('Not Reported')
		
		mapdic = {'Not Reported':'Not Reported'}
		for race in races:
			mapdic[race]=st.selectbox(f"[{race}]: For QC purppose, select the best match from the followings",
			["American Indian or Alaska Native", "Asian", "White", "Black or African American", 
			"Multi-racial", "Native Hawaiian or Other Pacific Islander", "Other", "Unknown"])
		df['race_for_qc'] = df.race_for_qc.map(mapdic)
		
		# cross-tabulation of study_arm and Phenotype
		st.text('=== race_for_qc X race ===')
		df['race'] = df.race.astype('str').fillna('_Missing')
		xtab = df.pivot_table(index='race_for_qc', columns='race', margins=True,
								values='sample_id', aggfunc='count', fill_value=0)
		st.write(xtab)
		if st.button("Confirm?"):
			st.info('Thank you!')
			race_conf=1

		# family history for qc
		st.subheader('Create "family_history_for_qc"')
		st.text(df.family_history.value_counts())
		family_historys = df.family_history.dropna().unique().astype('str')
		nmiss = sum(pd.isna(df.family_history))
		if nmiss>0:
			st.text(f'{nmiss} entries missing family_history')
			df['family_history_for_qc'] = df.family_history.astype('str').fillna('Not Reported')
		
		mapdic = {'Not Reported':'Not Reported'}

		if len(family_historys)>0:
			n_fhs = st.columns(len(family_historys))
			for i, x in enumerate(n_fhs):
				with x:
					fh = family_historys[i]
					mapdic[fh]=x.selectbox(f'[{fh}]: For QC, we only need "Yes", "No"',['Yes', 'No', 'Not Reported'], key=i)
		df['family_history_for_qc'] = df.family_history_for_qc.map(mapdic)

		# cross-tabulation of study_arm and Phenotype
		st.text('=== family_history_for_qc X family_history ===')
		df['family_history'] = df.family_history.astype('str').fillna('_Missing')
		xtab = df.pivot_table(index='family_history_for_qc', columns='family_history', margins=True,
								values='sample_id', aggfunc='count', fill_value=0)
		st.write(xtab)

		if st.button("Confirm?"):
			st.info('Thank you!')
			fh_conf=1
			
		# Plate Info
		st.subheader('Plate Info')
		df['Plate_name'] = df.Plate_name.astype('str').fillna('_Missing')
		xtab = df.pivot_table(index='Plate_name', 
							columns='study_arm', margins=True,
							values='sample_id', aggfunc='count', fill_value=0)
		st.write(xtab)

		for plate in df.Plate_name.unique():
			df_plate = df[df.Plate_name==plate].copy()
			df_plate_pos = df_plate.Plate_position
			# duplicated position check
			if plate!='_Missing':
				if len(df_plate_pos)>96:
					st.error('Please make sure, N of samples on plate [{plate}] is =<96')
					flag=1
				dup_pos = df_plate_pos[df_plate_pos.duplicated()].unique()
				if len(dup_pos)>0:
					st.error(f' !!!SERIOUS ERROR!!!  Plate position duplicated position {dup_pos} on plate [{plate}]')
					flag=1

		# Numeric values
		st.subheader('Numeric Values')
		numerics_cols = ['DNA_volume', 'DNA_conc', 'r260_280','age', 'age_of_onset', 'age_at_diagnosis']
		flag3 = 0
		for v in numerics_cols:
			if df.dtypes[v] not in ['float64', 'int64']:
				st.error(f'{v} is not numeric')
				flag=1
				flag3=1
		if flag3==0:
			st.text('Numeric chek --> OK. Check the distribution with the below button')

			if st.button("Check Distribution"):
				for v in numerics_cols:
					nmiss = df[v].isna().sum()
					vuniq = df[v].dropna().unique()
					nuniq = len(vuniq)
					if nuniq==0:
						st.text(f'{v} - All missing')
					elif nuniq==1:
						st.text(f'{v} - One value = {vuniq[0]}, ({nmiss} entries missing)')
					elif nuniq <6:
						st.write(df[v].value_counts(dropna=False))
					else:
						st.text(f'{v} - histgram ({nmiss} entries missing)')
						hist_values=np.histogram(df[v].dropna())[0]
						st.bar_chart(hist_values, )

		# Sample Submitter
		Submitter = st.text_input('Sample Submitter - First name initial + ". " + last name" (e.g.- H. Morris)')
		df['Submitter'] = Submitter

		if st.button("Finished?"):
			if not Submitter:
				st.error('Have you input the submitter?')
			elif flag==0:
				st.markdown(get_table_download_link(df), unsafe_allow_html=True)
			elif (ph_conf + race_conf + sex_conf + fh_conf)>0:
				st.error('Forget to confirm?')
			else:
				st.error('Please resolve all errors')



if __name__ == '__main__':
	main()

