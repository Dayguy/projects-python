import os, argparse, json 
from datetime import datetime
"""Reads a master JSON file looping over each record creating 1 file per REQUEST_ID value."""

def main(client, path, infile):

    date = datetime.today().strftime('_%Y%m%d_')

    if verbose:
        print('Opening source file: ' + path + infile)
    
    # Open and read input file
    try:
        with open(path + infile, 'r', encoding='utf-8') as input_file:
            for line in input_file:
                try:
                    record = json.loads(line)

                except:
                    if verbose:
                        # Assumed header/footer record
                        print('')
                        print('*** WARNING ***  Non-JSON record skipped:')
                        print(' ' * 5 + line)

                else:
                    output_file = 'YM_' + client + '_CCPA' + date + record["request_id"] + '.json'
                    if verbose:
                        print('Writing parsed file: ' + path + output_file)
                    
                    # Open and write output file
                    try:
                        with open(path + output_file, 'w+') as json_file:
                            json_file.write(json.dumps(record))
                    except:
                        print('Unable to write file: ' + path + output_file)

    except FileNotFoundError:
        print('File not found: ' + path + infile)

    

if __name__ == "__main__":

    # Process arguments
    parser = argparse.ArgumentParser(description='Generate 1 JSON file per REQUEST_ID found in the target file.')
    parser.add_argument('client', metavar = 'client', help = 'client code used in the file name, e.g. TYC')
    parser.add_argument('directory', metavar = 'path', help = 'working files directory')
    parser.add_argument('file', metavar = 'file', help = 'target file to be parsed')
    parser.add_argument('-c', '--clean', action='store_true', default=False, dest='boolean_clean', help = 'remove the target file after processing')
    parser.add_argument('-v', '--verbose', action='store_true', default=False, dest='verbose', help = 'turn on script output')
    args = parser.parse_args()

    # Global verbosity flag
    verbose = args.verbose
    if verbose:
        print('')

    # Call main() function
    main(client = args.client, path = args.directory, infile = args.file)
    
    # Remove original unparsed file
    if args.boolean_clean:
        try:
            os.remove(args.directory + args.file)
            if verbose:
                print('Removed source file: ' + args.directory + args.file)
        except FileNotFoundError:
            print('Unable to remove: ' + args.directory + args.file)
    if verbose:
        print('')
