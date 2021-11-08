# creating a mock QC file
nr = 500
n_full_plate = floor(nr / 96)
on_final_plate = nr-96*n_full_plate
plate_no= c(rep(1:(n_full_plate), each=96), rep(n_full_plate+1, on_final_plate))
full_plate_pos = paste0(rep(c('A', 'B', 'C', 'D', 'E', 'F', 'G', 'H'), 12), rep(1:12, each=8))
df = data.frame(
  study=rep('PDSTUDY',nr),
  sample_id = paste('sample_no_', 1:nr),
  sample_type = 'DNA',
  DNA_volume=rnorm(nr, 40, 5),
  DNA_conc = runif(nr, 0.5, 1.3),
  r260_280 = runif(nr, 1.3, 2.1),
  Plate_name = paste0('P', plate_no),
  Plate_position = c(rep(full_plate_pos, n_full_plate), full_plate_pos[1:on_final_plate]),
  clinical_id = paste0('MED', sample(1:100000, size = nr, replace = T)),
  study_arm = sample(c('Disease', 'Healthy'), nr, replace=T),
  sex = sample(c(1,2), nr, replace = T),
  race = sample(c(1,2,3,4,5, NA_integer_), nr, replace = T), 
  age = rnorm(nr, 68, 5),
  age_at_onset = NA_integer_)
df$age_at_diagnosis = df$age - runif(nr, 0.2, 8)
df$age_of_onset = (df$age + df$age_at_onset)/2
df$family_history = sample(c('N', 'Y', 'U', NA_character_), nr, replace = T)
df$region = sample(c('US', 'Japan', 'Canada', NA_character_), nr, replace = T)
df$comment = NA
df$alternative_id1=NA
df$alternative_id2=NA

write.csv(df, 'Document/PDSTUDY_sample_manifest.csv', col.names = F)
