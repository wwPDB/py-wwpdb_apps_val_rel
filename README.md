# py-wwpdb_apps_val_rel
Service to prepare weekly validation reports

## requirements
In site-config the following must be set

    VAL_REL_PROTOCOL = determines the protocol to use (ftp, http, https) if local ftp tree is not available.
    VAL_REL_ADMIN_EMAIL = comma separated list of who to contact on failures
    VAL_REL_DISABLE_MULTITHREAD = if set disable validation code from running in parallel fashion
    SITE_PDB_FTP_ROOT_DIR = the root of the PDB FTP tree (before pdb/data) - this can be not set if its not available at the local site 
    SITE_EMDB_FTP_ROOT_DIR = the root of the EMDB FTP tree (before emdb/structures) - this can be not set if its not available at the local site
    SITE_FTP_SERVER = this will default to ftp.wwpdb.org if not set
    SITE_FTP_SERVER_PREFIX = this is the prefix in the URL at the FTP server until you get to the PDB or EMDB data - i.e. on ftp.wwpdb.org this is "pub"
    SITE_HTTP_SERVER = this will default to files.wwpdb.org if not set
    SITE_HTTP_SERVER_PREFIX = this is the prefix in the URL at the HTTP server until you get to the PDB or EMDB data - i.e. on files.wwpdb.org this is "pub"
    SITE_RBMQ_SERVER_HOST = this is the host that runs the rabbitMQ server

## to setup rabbitMQ

See

    https://github.com/wwPDB/onedep-maintenance/blob/master/pdbe_redhat7/server_scripts/setup_rabbitMQ.sh
    
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
        --skip_emdb - if only PDB entry reports with no visual analysis is required.
        --entry_list - comma separated list of entries
        --entry_file - file containing entries, one per line
        --output_root - to output to a path of your choice
        --help for other options

This should be run on a cron every few hours.

If a priority queue is required, add the option --priority.

### 2) validation report workers
    
workers pick up work from the rabbitMQ queue and generate validation reports.
To start one worker

    python -m wwpdb.apps.val_rel.service.ValidationReleaseServiceHandler --start
    
To read from a priority queue, add the option --priority.

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

### 3) To find missing entries and queue for the following week
    
To find missing entries and write them out to a temporary file 

    python -m wwpdb.apps.val_rel.utils.find_and_run_missing --write_missing

then to read the temporary file and load the entries into the missing queue
    
    python -m wwpdb.apps.val_rel.utils.find_and_run_missing --read_missing

For priority queues, add --priority along with --read_missing.

### to run on a single entry without the rabbitMQ queue

    python -m wwpdb.apps.val_rel.ValidateRelease
    usage options are
        --pdbid - a single pdb id
        --emdbid - a single emdb id
        --output_root - to output to a path of your choice

### 4) Publishing and consuming from a priority queue

By default, the queues are not priority queues.

To make priority queues, pass an argument of --priority to PopulateValidateRelease, ValidationReleaseServiceHandler, and find_and_run_missing.

Priority queues cannot write to or read from non-priority queues, and an error is thrown if you attempt to mix them.

Therefore, an argument of --priority is always specified for priority queues.

The priority values are determined automatically, with higher values having higher priority.

- 10 missing
- 8 new pdb
- 6 new emdb
- 4 modified pdb
- 2 modified emdb
- 1 default


### 5) Subscription queues

By default, the queues are persistent queues that store messages regardless of the existence of producers or consumers.

However, even with priority queues, it's not possible to read a subset of messages with particular attributes, for example only emdb messages.

Therefore, subscription queues have been built which, if necessary, enable higher specificity.

Subscription queues publish to a larger number of exchanges and then subscribe to exchanges of choice.

To make subscription queues, pass an argument of --subscribe to PopulateValidateRelease and ValidationReleaseServiceHandler, followed by an exchange name which should be the same for both.

You must invoke the consumer before the producer or else the messages will be lost.

A subscription queue is only temporary until the consumer closes, therefore they are not intended to be relied upon exclusively, rather as a supplement to already existing queues.

Once the consumer is stopped, the queue and all of its contents will be deleted.

Subscription queues may have advantages during service peaks.

For example, to relieve congestion in the emdb folder, stop the regular producer crons, then start selective consumers with exchange names 'pdb_production_exchange' and 'emdb_production_exchange', then start corresponding producers with the same exchange names, one with option '--pdb_release' and one with option '--emdb_release'.

In the present system, subscription queues must not be run at the same time as the regular queues, at least not with the same options, or else they will both publish/consume the same files.

### 6) Debugging

ValidationReleaseServiceHandler runs a background process which is difficult to get debugging information from.

If errors occur from mixing of priority and non-priority queues, ValidationReleaseServiceHandler will not report them.

One possible side effect is that consumers will not stop when attempting to stop them with ValidationReleaseServiceHandler.

If consumers will not stop, pass an argument of --list to ValidationReleaseServiceHandler.

The running consumer process ids will be listed.

If it's possible to detect the processes that are responsible, delete all or some of the running process ids and their associated pid files.

The path to the pids file directory is printed out with each invocation of ValidationReleaseServiceHandler.
