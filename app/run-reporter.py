#!/usr/bin/env python3

from TrelloCollector import trello_collector
from GSpreadSheetExporter import gspreadsheet_exporter
from Transformer import data_transformer
from UpdateTrello import trello_updater

import logging
import tempfile
import os
import yaml
import argparse

import httplib2
from apiclient import discovery

def main():
    logger = logging.getLogger("sysengreporting")
    logger.setLevel(logging.DEBUG)

    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    _stdlog = logging.StreamHandler()
    _stdlog.setLevel(logging.DEBUG)
    _stdlog.setFormatter(formatter)

    logger.addHandler(_stdlog)

    parser = argparse.ArgumentParser()
    parser.add_argument('--config', help='report config', default="config/report.yml")
    parser.add_argument('--deep-scan', help='query each individual card', dest='deep_scan', action='store_true')
    parser.add_argument('--no-deep-scan', help='query each individual card', dest='deep_scan', action='store_false')
    parser.set_defaults(deep_scan=True);
    parser.add_argument('action', nargs='?', help='report to produce the report, list to output boards and lists', default="report")
    args = parser.parse_args();


    if os.path.isfile(args.config):
         with open(args.config, 'r') as stream:
             report_config = yaml.load(stream)
    else:
        logger.error('Invalid configuration file!')
        return;

    with open("secrets/trello_secret.yml", 'r') as stream:
        trello_secret_config = yaml.load(stream)


    warehouse = trello_collector.TrelloCollector(report_config, trello_secret_config)
    logger.info('Welcome to the Warehouse!')

    if args.action == 'list':
        warehouse.list_boards(); #output list of Trello boards and lists 
        return
    elif args.action == 'update_projects':
        unprocessed_report = warehouse.parse_trello(False);

        # Transform the Data
        transformer = data_transformer.DataTransformer(report_config, unprocessed_report, False)
        transformer.repopulate_report()
        updater = trello_updater.TrelloUpdater(transformer.dest_report, trello_secret_config)
        updater.update_projects()
        #warehouse.update_epics();
        return;
    elif args.action != 'report':
        logger.error('Unrecognized actions %s' % (args.action))
        return;


    unprocessed_report = warehouse.parse_trello(args.deep_scan);

    # Transform the Data
    transformer = data_transformer.DataTransformer(report_config, unprocessed_report, True)

    transformer.repopulate_report()

    #Write data to Google SpreadSheets
    exporter = gspreadsheet_exporter.GSpreadSheetExporter(report_config, "secrets/");
    exporter.write_spreadsheet(transformer.dest_report)
    #logger.debug('Report %s' % (transformer.dest_report))

if __name__ == '__main__':

    main()
