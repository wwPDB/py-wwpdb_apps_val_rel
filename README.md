# py-wwpdb_apps_val_rel
Service to prepare weekly validation reports

## requirements
In site-config the following must be set

    SITE_PDB_FTP_ROOT_DIR = the root of the PDB FTP tree (before pdb/data) 
    SITE_EMDB_FTP_ROOT_DIR = the root of the EMDB FTP tree (before emdb/structures)
    rabbitMQ server connection details
    
## usage

This process has two parts
1) finding entries to run validation reports and adding to a rabbitMQ queue
2) workers which take work from the rabbitMQ queue and create validation reports



### 1) Finding entries

Entries are found by a script which searches the for_release folder 

    python -m wwpdb.apps.val_rel.PopulateValidateRelease
    usage options are
        --pdb_release - find PDB entries in the for_release/{added/modified} folders  
        --emdb_release - find EMDB entries in the for_release/emd folder

This should be run on a cron every few hours

### 2) validation report workers
    
workers pick up work from the rabbitMQ queue and generate validation reports.
To start one worker

    python -m wwpdb.apps.val_rel.service.ValidationReleaseServiceHandler --start
    
To start several workers - below example starts 50 workers 

    for i in {1..50}
    do
        echo ${i}
        python -m wwpdb.apps.val_rel.service.ValidationReleaseServiceHandler --start --instance ${i}
    done
 
 To stop workers
 
    python -m wwpdb.apps.val_rel.service.ValidationReleaseServiceHandler --stop
    or
    python -m wwpdb.apps.val_rel.service.ValidationReleaseServiceHandler --stop --instance ${i}
