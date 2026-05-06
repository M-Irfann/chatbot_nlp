status_list = ['terbaik','loyal','jarang','sering']

time_list = ['hari','minggu','bulan','tahun']

time = None
status = None

sentence = "siapa pelanggan terbaik bulan ini"
sentence1 = "siapa pelanggan terbaik 3 bulan ini dan pelanggan paling jarang selama 2 bulan"

# print(status,time)

def extract_entity(text):

    result = {}

    words = text.split()

    for index, word, in enumerate(words):

        if word in status_list:
            result['status'] = word
        
        if word in time_list:

            if index+1 < len(words):
                result['time'] = word + " " + words[index+1]
            else:
                result['time'] = word
    print(result)

extract_entity(sentence1)
