# install packages
import pandas as pd 
import numpy as np
import datetime as dt 

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
          'age', 'age_of_onset', 'age_at_diagnosis', 'age_at_death', 'family_history',
          'region', 'comment', 'alternative_id1', 'alternative_id2', 
          'Phenotype','Genotyping_site', 'Sample_submitter', 'original_manifest']
  qc_cols= ['sex_for_qc', 'race_for_qc', 'family_history_for_qc', 'region_for_qc']
  origin_col = ['sex', 'race', 'family_history', 'region']
  
  # requirements
  nocols = np.setdiff1d(cols, data.columns)
  if len(nocols)>0:
    print('!!!SERIOUS ERROR!!! \nSome columns are missing')
    print('Missing columns:', nocols)
    return
  # qc in process?
  cols_qcing = np.intersect1d(qc_cols, data.columns)
  cols_not_qcing = np.setdiff1d(qc_cols, cols_qcing)
  if len(cols_qcing)>0:
    qcing = True
  else:
    qcing = False


  # start
  flag=0
  serious_error = 0

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
      serious_error=1
    else: 
      print('"dup_not_allowed=False" option is active')
      print('!!DUPLICATIONS IGNORED!!')

  # All have clinical ID?
  if sum(pd.isna(x2.clinical_id))>0:
    print('\n!!!SERIOUS ERROR!!! \nPlease provide clinical ID for all entries with sample IDs')
    print('N of entries with clinical ID missing:', sum(pd.isna(x2.clinical_id)))
    serious_error=1
  
  # set aside the original sex, race, region, family history and update origin_cols
  x2_origin = x2[origin_col].copy()
  if qcing:
    cols_update = [v.replace('_for_qc', '') for v in cols_qcing]
    x2[cols_update] = x2[cols_qcing].copy()
    print(f'Below, {cols_update} are referring to the "*_for_qc" variables')



  # Now ready for the more detailed QC
  # study_arm and Phenotype
  nmiss_study_arm = sum(pd.isna(x2.study_arm))
  if nmiss_study_arm>0: # fill na
    print('N of study_arm info missing --> recoded as "Not Reported":', nmiss_study_arm)
    x2['study_arm'] = x2.study_arm.fillna('Not Reported')
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
    print('\nsex info missing --> recoded as "Not Reported":', nmiss_sex)
    x2['sex'] = x2.sex.fillna('Not Reported')
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
    print('\nrace info missing --> recoded as "Not Reported":', nmiss_race)
    x2['race'] = x2.race.fillna('Not Reported')
    flag=1
  else:
    print('\nrace info: no missing')
  race_er = np.setdiff1d(x2.race.unique().astype('str'), ["American Indian or Alaska Native", "Asian", "White", "Black or African American", "Multi-racial", "Native Hawaiian or Other Pacific Islander", "Other", "Unknown", "Not Reported"])
  if len(race_er)>0:
    print('Undefined value:', race_er)
    flag=1
  print(x2.race.value_counts().to_frame())


  # family_history
  nmiss_fh = sum(pd.isna(x2.family_history))
  if nmiss_fh>0: # fill na
    print('\nfamily history info missing --> recoded as "Not Reported":', nmiss_fh)
    x2['family_history'] = x2.family_history.fillna('Not Reported')
    flag=1
  else:
    print('\nfamily history info: no missing')
  fh_er = np.setdiff1d(x2.family_history.unique().astype('str'), ["Yes", "No", "Unknown", "Not Reported"])
  if len(fh_er)>0:
    print('Undefined value:', fh_er)
    flag=1
  print(x2.family_history.value_counts().to_frame())


  # numeric parameter check
  print('\n')
  for v in ['age', 'age_of_onset', 'age_at_diagnosis', 'age_at_death']:
    if x2.dtypes[v] not in ['float64', 'int64']:
      print(f'ERROR: {v} needs to be numeric (or missing)')
      flag=1
    else:
      v_vec = x2[v].dropna()
      if len(v_vec)>0:
        print(f'{v} : {len(v_vec)} non-missing obs, min={np.min(v_vec)}, mean={np.mean(v_vec)}, max={np.max(v_vec)}')
      else:
        print(f'{v} is all missing')

  # Other missing check
  x2_non_miss_check = x2[['sample_id', 'study', 'sample_type', 'region', 'Genotyping_site', 'Sample_submitter']].copy()
  if x2_non_miss_check.isna().sum().sum()>0:
    print('\n!!!SERIOUS ERROR!!! \nMissing not allowed for the following columns. Please fill and repeat this process again.')
    print(x2_non_miss_check.info())
    serious_error=1

  # Genotyping_site check
  gs_er = np.setdiff1d(x2.Genotyping_site.unique().astype('str'), ['NIH', 'Fulgent'])
  if len(gs_er)>0:
    print('Undefined value:', fh_er)
    print('\n!!!SERIOUS ERROR!!! \nGenotyping_site is either NIH or Fulgent')
    serious_error=1

  # If shipping to Fulgent, Box ID and Well position determined? 
  x2_fulgent_non_miss_check = x2.loc[x2.Genotyping_site=='Fulgent', 
                                     ['sample_id', 'DNA_volume', 'DNA_conc',  'Plate_name', 'Plate_position']
                                     ].copy()
  if x2_fulgent_non_miss_check.isna().sum().sum()>0:
    print('\n!!!SERIOUS ERROR!!! \nThese are samples to Fulgent.\nMissing not allowed for the following columns. Please fill and repeat this process again.')
    print(x2_fulgent_non_miss_check.info())
    serious_error=1

  # Plate name, Position check
  print('\n==== Check N per plate/box (Usually less than 96) ====')
  x2_plate_fillna = x2.copy()
  x2_plate_fillna.Plate_name = x2_plate_fillna.Plate_name.fillna('Not Provided')
  for plate in x2_plate_fillna.Plate_name.unique():
    x2_plate = x2_plate_fillna[x2_plate_fillna.Plate_name==plate].copy()
    x2_plate_pos = x2_plate.Plate_position
    # duplicated position check
    if plate!='Not Provided':
      dup_pos = x2_plate_pos[x2_plate_pos.duplicated()].unique()
      if len(dup_pos)>0:
        print(f'\n!!!SERIOUS ERROR!!! \nPlate position duplicated - {dup_pos} on [{plate}]')
        serious_error = 1
  xtab = x2_plate_fillna.pivot_table(index='Plate_name', 
                      columns='Phenotype', margins=True,
                      values='sample_id', aggfunc='count', fill_value=0)
  print(xtab)

  if serious_error==1:
    print('please resolve errorss')
    return

  # current values to qc_cols
  x2[qc_cols] = x2[origin_col].copy()
  # recover original cols
  x2[origin_col] = x2_origin[origin_col].copy() 
    
  # return the data
  if flag==1:
    print('\n=============')
    print('Returning a dataframe with non-dup entries, non-missing IDs')
    print('Non-missing sex, race and family history are returned as "*_for_qc" variables)')
    print('Please work a little bit more...')
    return(x2.reset_index(drop=True)) # reset index

  if flag==0:
    print('\n=============\nWELL DONE! The dataset is ready to be assinged for GP2IDs')
    data_qced = x2.copy()
    data_qced['QC'] = 'PASS' # This column is required to provide giveGP2ID
    return (data_qced)
  
# function to convert numeric if possible (to avoid the program to tell 3011.0 and 3011 are different)
def convertNumeric(arr):
  # If the object can be converted to be numeric, then convert to numeric
  # If not, then keep the string.
  arr1 = pd.to_numeric(arr, errors='coerce')
  arr2 = np.where(pd.notna(arr1), arr1, arr)
  return(arr2)

####################################################################################

def giveGP2ID(data, manifest_id, list_non_finalized_mid = []):
  """
  This is a function to assign GP2ID to the data. 
  This will automatically read previous manifests of the study 
  and check the consistency.
  GP2ID - unique to clinicla_id
  GP2sampleID - unique to sample_id. 
      e.g. GP2ID_s1 = 1st sample. GP2ID_s2 = second sample and so on.
  If consistent, it saves the file to qcing folder as:
  {study_code}_sample_manifest_qced_{manifest_id}.csv
  * study_code is derived from the first row of data. If a different output surfix needed, 
  provide output_suffix and then {output_suffix}_sample_manifest_qced_{manifest_id}.csv
  # Not yet finalized manifests can be provided as list of manifest_id
  ## m1 and m2 are not finalized when doing qc for m3 --> list_non_finalized_mid = ['m1','m2']
  """
  # check the data was QCed
  if "QC" not in data.columns:
    print('\n!!!SERIOUS ERROR!!! \nThe data does not seem to be QCed.')
    return

  # preparation
  allx2 = pd.DataFrame()
  allx3 = pd.DataFrame()
  d = data.copy()
  d['manifest_id'] = manifest_id
  d['clinical_id'] = convertNumeric(d.clinical_id)
  mnum = int(manifest_id.replace('m', ''))
  study_codes = d.study.unique()
  if len(study_codes)>1:
    print('MULTIPLE STUDIES ARE DETECTED\n\n')
  
  for study_code in study_codes:
    x1 = d[d.study==study_code].copy()
    # summary
    uids = x1.clinical_id.unique()
    print(f'======== {study_code}_{manifest_id} =========')
    print('N of samples:', x1.shape[0])
    print('N of participants:', len(uids))

    
    # load previous manifest if available
    x0 = pd.DataFrame()
    if mnum > 1:
      for mnum_i in range(1,mnum):
        if f'm{mnum_i}' in list_non_finalized_mid:
          df_previous=pd.read_csv(f'/content/drive/Shared drives/GP2_data_repo/sample_manifest/qced/{study_code}_sample_manifest_qced_m{mnum_i}.csv')
          print(f'previous version - m{mnum_i}: nrow = {df_previous.shape[0]} - !!Note the manifest not finalized - loaded from the "qced" folder')
          
        else:
          df_previous=pd.read_csv(f'/content/drive/Shared drives/GP2_data_repo/sample_manifest/finalized/{study_code}_sample_manifest_qced_m{mnum_i}.csv')
          print(f'previous version - m{mnum_i}: nrow = {df_previous.shape[0]}')

        df_previous['manifest_id']=f'm{mnum_i}'
        df_previous['clinical_id']=convertNumeric(df_previous['clinical_id'])
        x0 = x0.append(df_previous)
          
    # create mapping dictionary (mapid) of clinical id --> uid_idx
    if len(x0)>0: ## retrieve previous mapping
      uid_idx_previous = x0.GP2ID.str.split('_', expand=True).iloc[:,1].astype('int')
      mapid = {clin:i for (clin,i) in zip(x0.clinical_id, uid_idx_previous)}
      n=max(list(mapid.values()))+1 # uid_idx to use for new clinical_id

      # update uids for the current data
      uids_new = np.setdiff1d(uids, list(mapid.keys()))
      print('N of new participants not in the previous manifests:', len(uids_new))
      uids = uids_new # update

    else:
      n=1
      mapid = {}
    
    # allocated uid_idx for new participants
    for uid in uids:
      mapid[uid]= n
      n += 1

    # map the sequencial number and create GP2IDs
    x2 = pd.concat([x0,x1], ignore_index=True)
    x2['uid_idx'] = x2.clinical_id.map(mapid)
    x2['GP2ID'] = [f'{study_code}_{i:06}' for i in x2.uid_idx]

    # unique sample ID for GP2sampleID
    x2['uid_idx_cumcount'] = x2.groupby('GP2ID').cumcount() + 1
    x2['GP2sampleID'] = x2.GP2ID + '_s' + x2.uid_idx_cumcount.astype('str')
    x2['SampleRepNo'] = 's' + x2.uid_idx_cumcount.astype('str')
    x2 = x2.reset_index(drop=True)


    # Table for Sample Number values
    x2['manifest'] = x2.study + '_' + x2.manifest_id
    print('\n====================')
    xtab = x2.pivot_table(index='manifest', columns='SampleRepNo', margins=True,
                          values='GP2sampleID', aggfunc='count', fill_value=0)
    print(xtab)

    # Table for Phenotypes
    print('\n====================')
    xtab = x2.pivot_table(index='manifest', columns='Phenotype', margins=True,
                          values='GP2sampleID', aggfunc='count', fill_value=0)
    print(xtab)

    # drop temporary variables
    x2 = x2.drop(columns=['uid_idx', 'uid_idx_cumcount', 'manifest', 'QC'])
    x3 = x2.loc[x2.manifest_id==manifest_id].copy().reset_index(drop=True)
    

    # Return the results
    output_file = f'{study_code}_sample_manifest_qced_{manifest_id}.csv'
    output_path = f'/content/drive/Shared drives/GP2_data_repo/sample_manifest/qced/{output_file}'
    print(f'\nSaved the GP2ID assigned table at [sample_manifest/qced] folder as: \n  * [{output_file}]\n')

    x3.to_csv(output_path, index=False)

    allx2 = allx2.append(x2)
    allx3 = allx3.append(x3)

  if len(study_codes)>1:
    output_file = f'{("_").join(study_codes)}_sample_manifest_qced_{manifest_id}.csv'
    output_path = f'/content/drive/Shared drives/GP2_data_repo/sample_manifest/qced/{output_file}'
    print(f'\nAdditionaly. saving the GP2ID assigned table of all samples from {("+").join(study_codes)} at [sample_manifest/qced] folder as: \n  * [{output_file}]')
    allx3.to_csv(output_path, index=False)
  
  print(f'The DataFrame of all samples from {("+").join(study_codes)} including those from the previous manifests is returned for further checking')
  return allx2

##################################################################################################################

def compare_consistency(target, reference, 
                        cols_to_compare=['study', 'sample_id', 'clinical_id', 
                                         'GP2sampleID', 'GP2ID', 
                                         'manifest_id', 'original_manifest']):
  """
  This fuction compares the target DataFrame against the reference DataFrame.
  The defalut setting of the cols_to_compare
  ['study', 'sample_id', 'clinical_id', 'GP2sampleID', 'GP2ID', 'manifest_id', 'original_manifest']
  If you would like to test the overall consistency, use all columns like - 
  cols_to_compare = target.columns
  """
  print(f'Target DF shape  : {target.shape}')
  df = target[cols_to_compare]
  n_df = df.shape[0]
  df=df.apply(convertNumeric, axis=0)
  print(f'Refrence DF shape: {reference.shape}')
  ref = reference[cols_to_compare]
  ref=ref.apply(convertNumeric, axis=0)
  n_ref = ref.shape[0]
  df['source']='target'
  ref['source']='reference'
  
  dfall = pd.concat([df, ref], axis=0, ignore_index=True)
  
  dfuniq= dfall.drop_duplicates(subset=dfall.columns[:-1]) # remove duplicates == entries in old should be duplicated in new
  n_uniq = dfuniq.shape[0]

  if n_df == n_uniq:
    print('\nThe file is consistent with the previous version.')
    print(f'N_total = {n_df}')
    print(f'N_new   = {n_df - n_ref}')

    # create version
    today = dt.datetime.today()
    version = f'{today.year:04d}{today.month:02d}{today.day:02d}'
    filepath=f'/content/drive/Shared drives/GP2_data_repo/sample_manifest/master_sheet/GP2sampleID_{version}_draft.csv'
    print(f'The table was saved as\n  {filepath}')
    target.to_csv(filepath, index=False)
  else:
    print('\n!!!ERRROR!!!\nNew file is inconsistent with the previous version.\n')
    df_diff = dfall.drop_duplicates(subset=dfall.columns[:-1], keep=False).sort_values(['GP2sampleID', 'source']).copy()
    print('===== Number of different entries (consistent entries were removed) ========')
    print(df_diff.pivot_table(index='study', columns='source', values='GP2sampleID', aggfunc='count'))
    print(f'\nInconsisctency entries and new entries are returned')
    return df_diff.reset_index(drop=True)