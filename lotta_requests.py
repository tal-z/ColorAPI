import multiprocessing
import requests

s = requests.session()

def call_endpoint(url):
    headers = {
    'content-type': 'application/json',
    'Authorization': 'Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpZCI6MX0.zP4UTqFfrpOp5H_T_EGwT4ifQFH08yZAFS5VRrwcohw'
            }
    response = s.post(url, headers=headers)
    print(response.status_code)

if __name__ == '__main__':
    pool = multiprocessing.Pool(4)
    ep = 'http://127.0.0.1:8000/extract/3/?name=Palaeobranchiostoma_hamatotergum&url=https%3A%2F%2Fupload.wikimedia.org%2Fwikipedia%2Fcommons%2Fthumb%2Fc%2Fc2%2FNarcissus_%2527Ice_Follies%2527_02.jpg%2F1024px-Narcissus_%2527Ice_Follies%2527_02.jpg'
    endpoints = [ep]*100
    pool.map(call_endpoint, endpoints)
