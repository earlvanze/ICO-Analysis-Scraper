def append_to_gsheet(output_data, gsheet_id, range_name):
    creds = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server()
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    service = build('sheets', 'v4', credentials=creds)

    # Call the Sheets API
    body = {
        'values': output_data
    }
    try:
        result = service.spreadsheets().values().append(
            spreadsheetId=gsheet_id, range=range_name,
            valueInputOption='USER_ENTERED', body=body).execute()
        message = ('{0} rows updated.'.format(DictQuery(result).get('updates/updatedRows')))
        return message
    except Exception as err:
        traceback.print_exc()
        return json.loads(err.content.decode('utf-8'))['error']['message']


def empty_folder(icos_folder):
    try:
        shutil.rmtree(icos_folder)
    except:
        traceback.print_exc()
        pass


# Used to search for keys in nested dictionaries and handles when key does not exist
# Example: DictQuery(dict).get("dict_key/subdict_key")
class DictQuery(dict):
    def get(self, path, default = None):
        keys = path.split("/")
        val = None

        for key in keys:
            if val:
                if isinstance(val, list):
                    val = [ v.get(key, default) if v else None for v in val]
                else:
                    val = val.get(key, default)
            else:
                val = dict.get(self, key, default)

            if not val:
                break;

        return val


# Returns empty string if s is None
def xstr(s):
    if s is None:
        return ''
    return str(s)