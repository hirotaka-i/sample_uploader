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
	menu = ["For Fulgent", "For NIH"]
	choice = st.sidebar.selectbox("Menu",menu)
	flag=0
	ph_conf=''
	sex_conf=''
	race_conf = ''
	fh_conf=''
	cols = ['study', 'sample_id', 'sample_type',
		'DNA_volume', 'DNA_conc', 'r260_280',
		'Plate_name', 'Plate_position', 'clinical_id', 
		'study_arm', 'sex', 'race', 
		'age', 'age_of_onset', 'age_at_diagnosis', 'family_history',
		'region', 'comment', 'alternative_id1', 'alternative_id2']
	required_cols = ['study', 'sample_id', 'sample_type', 'clinical_id','study_arm', 'sex']
	allowed_samples=['Blood (EDTA)', 'Blood (ACD)', 'Blood', 'DNA', 
					'DNA from blood', 'DNA from FFPE', 'RNA', 'Saliva', 
					'Buccal Swab', 'T-25 Flasks (Amniotic)', 'FFPE Slide',
					'FFPE Block', 'Fresh tissue', 'Frozen tissue', 
					'Bone Marrow Aspirate', 'Whole BMA', 'CD3+ BMA', 'Other']
	fulgent_cols = ['DNA_volume', 'DNA_conc', 'Plate_name', 'Plate_position']
	data_file = st.sidebar.file_uploader("Upload Sample Manifest (CSV/XLSX) [Currently only CSV!]", type=['csv', 'xlsx'])
	

	st.title("GP2 sample manifest self-QC web app")
	st.text('This is a web app to self-check the sample manifest')
	st.text('The template download from the below link (go to "File"> "Download" as xlsx/csv)')
	st.write('https://docs.google.com/spreadsheets/d/1ThpUVBCRaPdDSiQiKZVwFpwWbW8mZxhqurv7-jBPrM4')
	st.text('Please refer to the second tab (Dictionary) for instruction')
	st.text('')
	if data_file is not None:
		st.header("Data Check and self-QC")
		# for debug purpose. get the file detail
		# file_details = {"Filename":data_file.name,"FileType":data_file.type,"FileSize":data_file.size}
		# st.write(file_details)
		
		# read a file
		df = read_file(data_file)
		df['race_for_qc'] = df.race.fillna('Not Reported')
		df['family_history_for_qc'] = df.family_history.fillna('Not Reported')
		df['region_for_qc'] = df.region.fillna('Not Reported')
		df['Genotyping_site'] = choice.replace('For ', '')
		if choice=='For Fulgent':
			required_cols = required_cols + fulgent_cols
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

		# sample type check
		st.text('sample_type check')
		st.write(df.sample_type.value_counts())
		not_allowed = np.setdiff1d(df.sample_type.unique(), allowed_samples)
		if len(not_allowed)>0:
			st.error(f'sample_type: {not_allowed} not allowed.')
			sample_list = '\n * '.join(allowed_samples)
			st.text(f'Allowed sample list - \n * {sample_list}')
			flag=1



		# study_arm --> Phenotype
		st.subheader('Create "Phenotype"')
		st.text('Count per study_arm')
		st.write(df.study_arm.value_counts())
		arms=df.study_arm.dropna().unique()
		n_arms = st.columns(len(arms))
		phenotypes={}
		for i, x in enumerate(n_arms):
			with x:
				arm = arms[i]
				phenotypes[arm]=x.selectbox(f"[{arm}]: For QC, please pick the closest Phenotype",["PD", "Control", "Prodromal", "Other", "Not Reported"], key=i)
		df['Phenotype'] = df.study_arm.map(phenotypes)

		# cross-tabulation of study_arm and Phenotype
		st.text('=== Phenotype x study_arm===')
		xtab = df.pivot_table(index='Phenotype', columns='study_arm', margins=True,
								values='sample_id', aggfunc='count', fill_value=0)
		st.write(xtab)
		
		ph_conf = st.checkbox('Confirm Phenotype?')
		if ph_conf:
			st.info('Thank you')
		

		# sex for qc
		st.subheader('Create "sex_for_qc"')
		st.text('Count per sex group')
		st.write(df.sex.value_counts())
		sexes=df.sex.dropna().unique()
		n_sexes = st.columns(len(sexes))
		mapdic={}
		for i, x in enumerate(n_sexes):
			with x:
				sex = sexes[i]
				mapdic[sex]=x.selectbox(f"[{sex}]: For QC, please pick a word below", 
									["Male", "Female", "Intersex", "Unknown", "Other", "Not Reported"], key=i)
		df['sex_for_qc'] = df.sex.replace(mapdic)

		# cross-tabulation of study_arm and Phenotype
		st.text('=== sex_for_qc x sex ===')
		xtab = df.pivot_table(index='sex_for_qc', columns='sex', margins=True,
								values='sample_id', aggfunc='count', fill_value=0)
		st.write(xtab)
		
		sex_conf = st.checkbox('Confirm sex_for_qc?')
		if sex_conf:
			st.info('Thank you')

		# race for qc
		st.subheader('Create "race_for_qc"')
		st.text('Count per race (Not Reported = missing)')
		st.write(df.race.value_counts())
		races = df.race.dropna().unique()
		nmiss = sum(pd.isna(df.race))

		if nmiss>0:
			st.text(f'{nmiss} entries missing race...')
			
		
		mapdic = {'Not Reported':'Not Reported'}
		for race in races:
			mapdic[race]=st.selectbox(f"[{race}]: For QC purppose, select the best match from the followings",
			["American Indian or Alaska Native", "Asian", "White", "Black or African American", 
			"Multi-racial", "Native Hawaiian or Other Pacific Islander", "Other", "Unknown", "Not Reported"])
		df['race_for_qc'] = df.race_for_qc.map(mapdic)
		
		# cross-tabulation
		st.text('=== race_for_qc X race ===')
		dft = df.copy()
		dft['race'] = dft.race.fillna('_Missing')
		xtab = dft.pivot_table(index='race_for_qc', columns='race', margins=True,
								values='sample_id', aggfunc='count', fill_value=0)
		st.write(xtab)
		
		race_conf = st.checkbox('Confirm race_for_qc?')
		if race_conf:
			st.info('Thank you')
		

		# family history for qc
		st.subheader('Create "family_history_for_qc"')
		st.text('Count per family_history category (Not Reported = missing)')
		st.write(df.family_history_for_qc.value_counts())
		family_historys = df.family_history.dropna().unique()
		nmiss = sum(pd.isna(df.family_history))

		if nmiss>0:
			st.text(f'{nmiss} entries missing family_history')
		mapdic = {'Not Reported':'Not Reported'}

		if len(family_historys)>0:
			n_fhs = st.columns(len(family_historys))
			for i, x in enumerate(n_fhs):
				with x:
					fh = family_historys[i]
					mapdic[fh]=x.selectbox(f'[{fh}]: For QC, any family history?',['Yes', 'No', 'Not Reported'], key=i)
		df['family_history_for_qc'] = df.family_history_for_qc.map(mapdic)

		# cross-tabulation 
		st.text('=== family_history_for_qc X family_history ===')
		dft = df.copy()
		dft['family_history'] = dft.family_history.fillna('_Missing')
		xtab = df.pivot_table(index='family_history_for_qc', columns='family_history', margins=True,
								values='sample_id', aggfunc='count', fill_value=0)
		st.write(xtab)

		fh_conf = st.checkbox('Confirm family_history_for_qc?')
		if fh_conf:
			st.info('Thank you')


		# region for qc
		st.subheader('Create "region_for_qc"')
		st.text('Count per region (Not Reported = missing)')
		st.write(df.region_for_qc.value_counts())
		regions = df.region.dropna().unique()
		nmiss = sum(pd.isna(df.region))
		if nmiss>0:
			st.text(f'{nmiss} entries missing for region')
		
		mapdic = {'Not Reported':'Not Reported'}

		if len(regions)>0:
			st.text('if ISO 3166-3 is available for the region, please provide')
			st.write('https://en.wikipedia.org/wiki/ISO_3166-1_alpha-3')
			n_rgs = st.columns(len(regions))
			for i, x in enumerate(n_rgs):
				with x:
					region = regions[i]
					mapdic[region]=x.text_input(f'[{region}] in 3 LETTER (or NA)')
		df['region_for_qc'] = df.region_for_qc.map(mapdic)

		# cross-tabulation 
		st.text('=== region_for_qc X region ===')
		dft = df.copy()
		dft['region'] = dft.region.fillna('_Missing')
		xtab = dft.pivot_table(index='region_for_qc', columns='region', margins=True,
								values='sample_id', aggfunc='count', fill_value=0)
		st.write(xtab)

		rg_conf = st.checkbox('Confirm regino_for_qc?')
		if rg_conf:
			st.info('Thank you')





		# Plate Info
		st.subheader('Plate Info')
		dft = df.copy()
		dft['Plate_name'] = dft.Plate_name.fillna('_Missing')
		xtab = dft.pivot_table(index='Plate_name', 
							columns='study_arm', margins=True,
							values='sample_id', aggfunc='count', fill_value=0)
		st.write(xtab)

		for plate in dft.Plate_name.unique():
			df_plate = dft[dft.Plate_name==plate].copy()
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
		st.subheader('Sample Submitter')
		Submitter = st.text_input('First name initial + ". (dot&space)" + last name" (e.g.- H. Morris)')
		df['Sample_submitter'] = Submitter

		if st.button("Finished?"):
			st.text("If everything is good, you will see the download link for the qced data")
			if flag==1:
				st.error('Some errors still exist (red comment). Please check the original data for missing etc')
			elif not Submitter:
				st.error('Have you input the submitter?')
			elif not (ph_conf & sex_conf & race_conf & fh_conf & rg_conf):
				st.error('Forget to confirm?')
			else:
				st.markdown(get_table_download_link(df), unsafe_allow_html=True)

# git add app.py;git commit -m "debug";git push -u origin main

if __name__ == '__main__':
	main()

