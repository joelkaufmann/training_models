from azure.storage.filedatalake import DataLakeServiceClient
import os
import pandas as pd
from dotenv import load_dotenv, find_dotenv
import io

_ = load_dotenv(find_dotenv())
key = os.getenv("AZURE_CONNECTION_STRING")
service_client = DataLakeServiceClient.from_connection_string(conn_str=key)

# Get the file system client
container_client = service_client.get_file_system_client(file_system="data-sherpa")

def download_csv_files(path, li=None, downloaded_files=None):
    if li is None:
        li = []
    if downloaded_files is None:
        downloaded_files = set()

    files = container_client.get_paths(path=path)

    for file in files:
        if file.name.endswith('.csv') and file.name not in downloaded_files:
            download = container_client.get_file_client(file.name).download_file()
            downloaded_bytes = download.readall()
            df = pd.read_csv(io.StringIO(downloaded_bytes.decode('utf-8'))).infer_objects()
            df['datetime'] = pd.to_datetime(df['datetime'])
            df.set_index('datetime', inplace=True)
            li.append(df)
            downloaded_files.add(file.name)
        elif file.is_directory:
            download_csv_files(file.name, li, downloaded_files)
    return li

def create_one_df(list):
    new_li = []
    i=0
    j=1
    while i < len(list):
        new_df = pd.concat([list[i], list[j]], axis=1)
        new_li.append(new_df)
        i += 2
        j += 2
    df = new_li[0].combine_first(new_li[1])
    i =2

    while i < len(new_li):
        df = df.combine_first(new_li[i])

        i += 1
    return df
#######################
# Load data
loaded_df = create_one_df(download_csv_files("sensor_data/2024"))