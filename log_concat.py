def update_logs(instance):
    import os
    import shutil
    import pandas as pd
    import csv

    instance.logger.removeHandler(instance.DuoHandler)
    filename = instance.filename
    year_folder = filename.split()[1].split('_')[0]
    filepath = f"./login-log/{year_folder}/{filename}"

    # ✅ Ensure destination folder exists
    os.makedirs(os.path.dirname(filepath), exist_ok=True)

    if os.path.exists(filename):
        # Move csv file to temp folder
        os.makedirs("./temp", exist_ok=True)
        temp = f"./temp/{filename}"
        shutil.move(filename, temp)

        print(f"\n\nReading update file: {filename}...\n\n")
        with open(temp, "r", newline="", encoding="utf-8") as file:
            reader = csv.reader(file)
            for row in reader:
                print(row)
        print(f"\n-------------- End of file '{filename}' --------------\n\n")

        if os.path.exists(filepath):
            df_old = pd.read_csv(filepath, index_col=False, encoding="utf-8")
            df_update = pd.read_csv(temp, index_col=False, encoding="utf-8")
            df_new = pd.concat([df_old, df_update])
            df_new.drop_duplicates(inplace=True)
            df_new.to_csv(filepath, index=False, encoding="utf-8")
        else:
            shutil.move(temp, filepath)

        shutil.rmtree("./temp")
    else:
        print("New logs do not exist.")
