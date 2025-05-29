import pandas as pd

try:
    df_jobs = pd.read_csv('remoteok_jobs_data.csv')
    print("Successfully loaded remoteok_jobs_data.csv into a DataFrame!")
    print(f"Number of jobs loaded: {len(df_jobs)}")
    print("\nFirst few jobs:")
    print(df_jobs.head())
    print("\nDataFrame Info:")
    df_jobs.info()
except FileNotFoundError:
    print("Error: remoteok_jobs_data.csv not found. Make sure it's in the correct directory.")
except Exception as e:
    print(f"An error occurred while loading the CSV: {e}")