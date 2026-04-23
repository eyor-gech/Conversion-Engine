from datasets import load_dataset
 
ds = load_dataset("hakunamatata1997/Layoffs_Data")
df = ds["train"].to_pandas()

df.to_csv("data/layoffs.csv", index=False)