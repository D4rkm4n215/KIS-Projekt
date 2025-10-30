import os
import json 
import collections

def add_new_key(key, val):
    abspath = os.path.abspath(__file__)
    dname = os.path.dirname(abspath)
    for json_file in os.listdir(dname):
        if json_file.endswith(".json"):
            file_path = os.path.join(dname, json_file)
            with open(file_path, encoding='utf-8') as f:
                d = json.load(f)
                f.close()
            d[key] = val
            od = collections.OrderedDict(sorted(d.items()))
            with open(file_path, 'w', encoding='utf8') as fp:
                json.dump(od, fp, indent=4, ensure_ascii=False)


if __name__ == "__main__":    
    add_new_key("DASHBOARD_TITLE_WBC", "White Blood Cells")
    add_new_key("DASHBOARD_TITLE_RBC", "Red Blood Cells")
    add_new_key("DASHBOARD_TITLE_PLATELES", "Platelets")
    add_new_key("DASHBOARD_TITLE_HGB", "Haemoglobin")
    add_new_key("DASHBOARD_TITLE_HCT", "Hematocrit")