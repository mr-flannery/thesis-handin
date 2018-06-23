import math
import random
from functools import reduce
import os
import argparse


def csv_field_wrap(field):
    return '"' + field.replace('"', '""') + '"'


def zeroPadString(inputString, targetLength):
    outputString = inputString
    for i in range(0, targetLength - len(inputString)):
        outputString = "0" + outputString
    return outputString


def generate_record(sample_data, costCenter, aufnr):
    record = []
    columns = [x for x in sample_data]

    for column in columns:
        if column == "RCNTR":
            record.append(csv_field_wrap(costCenter))
        elif column == "AUFNR":
            record.append(csv_field_wrap(aufnr))
        elif column == "KOKRS":
            record.append(csv_field_wrap("0001"))
        elif column == "RACCT":
            record.append(csv_field_wrap("0000400000"))
        else:
            sample_value = sample_data[column][random.randint(0, len(sample_data[column]) - 1)]
            record.append(csv_field_wrap(sample_value))
    return record


def generate(sample_data, args):
    setnode = []
    setleaf = []
    columns = [x for x in sample_data]
    cc_per_hierarchy = int(math.pow(2, args.hierarchyDepth)) - 1

    if not os.path.exists(args.outputDirectory):
        os.makedirs(args.outputDirectory)

    output_file_name = args.outputDirectory + "generated_" + args.samplePath

    with open(output_file_name, "w") as file:
        file.write(",".join(list(map(lambda x: csv_field_wrap(x), columns))))
        file.write("\n")

        for i in range(0, args.selectivitySteps):
            print("selectivity step: " + str(i+1) + " of " + str(args.selectivitySteps))
            selectivity_prefix = zeroPadString(str(i+1), len(str(args.selectivitySteps)))

            for j in range(0, cc_per_hierarchy):
                cc_prefix = zeroPadString(str(j), len(str(cc_per_hierarchy)))
                cost_center = selectivity_prefix + cc_prefix
                cost_center_h = "H" + cost_center

                if j == 0:
                    setnode.append(('', cost_center_h))
                else:
                    setnode.append(("H" + selectivity_prefix + zeroPadString(str(int((j-1)/2)), len(str(cc_per_hierarchy))), cost_center_h))
                setleaf.append((cost_center_h, cost_center))

                for k in range(0, args.aufnrPerCc):
                    print(str(k))
                    aufnr = selectivity_prefix + cc_prefix + zeroPadString(str(k+1), len(str(args.aufnrPerCc)))

                    temp_records = []
                    for l in range(0, args.recordsPerAufnr):
                        temp_records.append(generate_record(sample_data, cost_center, aufnr))

                    file.write(
                        reduce(lambda x,y: x+y, map(lambda x: ",".join(x) + "\n", temp_records)))  # magicOneLiner

            # connect the hierarchies
            if i < args.selectivitySteps - 1:
                setnode.append((cost_center_h, "H" + zeroPadString(str(i+2), len(str(args.selectivitySteps))) + "00"))

    write_setleaf_csv(args, setleaf)
    write_setnode_csv(args, setnode)
    write_sql_auth_setup_files(args, cc_per_hierarchy, setleaf)



def write_sql_auth_setup_files(args, cc_per_hierarchy, setleaf):
    co_action_stmt = "INSERT INTO EVAL.UST12 (MANDT, OBJCT, AUTH, AKTPS, FIELD, VON, BIS) VALUES ('012','K_CCA','HIER','A','CO_ACTION','3027','');"
    kstar_stmt = "INSERT INTO EVAL.UST12 (MANDT, OBJCT, AUTH, AKTPS, FIELD, VON, BIS) VALUES ('012','K_CCA','HIER','A','KSTAR','0000400000','');"
    ust12_implicit_template = "INSERT INTO EVAL.UST12 (MANDT, OBJCT, AUTH, AKTPS, FIELD, VON, BIS) VALUES ('012','K_CCA','HIER','A','RESPAREA','HI0001{}','');"

    ust12_explicit_stmts = get_ust12_stmts(setleaf)
    usrbf2_stmts = get_usrbf2_stmts()

    for j in range(1, args.selectivitySteps + 1):
        dir_name = "selectivity-" + str(j / args.selectivitySteps)
        if not os.path.exists(args.outputDirectory + dir_name):
            os.makedirs(args.outputDirectory + dir_name)
        with open(args.outputDirectory + dir_name + "/explicit-auth-setup.sql", "w") as file:
            for stmt in usrbf2_stmts:
                file.write(stmt)
                file.write("\n")
            file.write(co_action_stmt)
            file.write("\n")
            file.write(kstar_stmt)
            file.write("\n")
            for i in range(len(ust12_explicit_stmts) - j * cc_per_hierarchy, len(ust12_explicit_stmts)):
                file.write(ust12_explicit_stmts[i])
                file.write("\n")
        with open(args.outputDirectory + dir_name + "/implicit-auth-setup.sql", "w") as file:
            for stmt in usrbf2_stmts:
                file.write(stmt)
                file.write("\n")
            file.write(co_action_stmt)
            file.write("\n")
            file.write(kstar_stmt)
            file.write("\n")
            file.write(
                ust12_implicit_template.format("H" + zeroPadString(str(j), len(str(args.selectivitySteps))) + "00"))


            # check for CSV import into HANA


def get_ust12_stmts(setleaf):
    ust12_explicit_template = "INSERT INTO EVAL.UST12 (MANDT, OBJCT, AUTH, AKTPS, FIELD, VON, BIS) VALUES ('012','K_CCA','HIER','A','RESPAREA','KS0001{}','');"
    ust12_explicit_stmts = []
    for entry in setleaf:
        ust12_explicit_stmts.append(ust12_explicit_template.format(entry[1]))
    return ust12_explicit_stmts


def get_usrbf2_stmts():
    usrbf2_template = "INSERT INTO EVAL.USRBF2 (MANDT, BNAME, OBJCT, AUTH) VALUES ('012','{}','K_CCA','HIER');"
    usrbf2_stmts = []
    usrbf2_stmts.append(usrbf2_template.format("USER"))
    for i in range(0, 99):
        usrbf2_stmts.append(usrbf2_template.format("USER_" + str(i)))
    return usrbf2_stmts


def write_setnode_csv(args, setnode):
    setnode_header = ["MANDT", "SETCLASS", "SUBCLASS", "SETNAME", "LINEID", "SUBSETCLS", "SUBSETSCLS", "SUBSETNAME",
                      "SEQNR"]
    setnode_records = []
    for entry in setnode:
        setnode_records.append(["012", "0101", "0001", entry[0], "1", "0101", "0001", entry[1], "1"])
    with open(args.outputDirectory + "setnode.csv", "w") as file:
        file.write(",".join(list(map(lambda x: csv_field_wrap(x), setnode_header))))
        file.write("\n")
        for record in setnode_records:
            file.write(",".join(list(map(lambda x: csv_field_wrap(x), record))))
            file.write("\n")


def write_setleaf_csv(args, setleaf):
    setleaf_header = ["MANDT", "SETCLASS", "SUBCLASS", "SETNAME", "LINEID", "VALSIGN", "VALOPTION", "VALFROM", "VALTO",
                      "SEQNR"]
    setleaf_records = []
    for entry in setleaf:
        setleaf_records.append(["012", "0101", "0001", entry[0], "0000000001", "I", "EQ", entry[1], entry[1], "1"])
    with open(args.outputDirectory + "setleaf.csv", "w") as file:
        file.write(",".join(list(map(lambda x: csv_field_wrap(x), setleaf_header))))
        file.write("\n")
        for record in setleaf_records:
            file.write(",".join(list(map(lambda x: csv_field_wrap(x), record))))
            file.write("\n")


def prepare_sample_data(path):
    columns = []
    data = {}
    fixed_columns = {"RCNTR", "AUFNR", "KOKRS", "RACCT"}

    with open(path, "r") as file:
        for line in file:
            if len(columns) == 0:
                columns = list(set(map(lambda x: x.replace("\"", ""), line[0:len(line)-1].split(","))).union(
                    fixed_columns))
                for column in columns:
                    data[column] = []
            else:
                record = list(map(lambda x: x.replace("\"", ""), line[0:len(line)-1].split(",")))
                for i in range(0, len(columns)):
                    data[columns[i]].append(record[i])

    return data


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate a dataset and corresponding authorizations from a sample dataset.")
    parser.add_argument('samplePath', type=str, help='Path to the sample CSV file')
    parser.add_argument('recordsPerAufnr', type=int, help='Number of records per internal order.')
    parser.add_argument('aufnrPerCc', type=int, help='Number of internal orders per cost center.')
    parser.add_argument('hierarchyDepth', type=int, help='Depth of the generated cost center hierarchies.')
    parser.add_argument('selectivitySteps', type=int, help='Number of selectivity steps (the data will be generated '
                                                           'such that there is an equal amount of records '
                                                           'per selectivity step).')
    parser.add_argument('outputDirectory', type=str, nargs='?', default='output/', help='Directory where the output '
                                                                                        'files are stored to. Defaults to \"output/\".')
    args = parser.parse_args()
    generate(prepare_sample_data(args.samplePath), args)
