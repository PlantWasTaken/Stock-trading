import pandas as pd
import yfinance as yf
import mplfinance as mpf
import json
import numpy as np
import time as t

ticker = open('Ticker.txt', "r")
log = open('log.txt', "a") 

ticker_lines = 0

def json_file_formatting():
    global ticker_lines

    with open('sim.json', 'r') as jsonFile:
        json_data = json.load(jsonFile)

    with open('sim.json', "w") as jsonFile:
        for ticker_lines, i in enumerate(ticker):
            if(i[-1:] == "\n"):
                json_data["Index"][str(i[:-1])] = {
                    "Stock": 0,
                    "Price": 0,
                    "cPrice": 0
                }
            else:
                json_data["Index"][str(i)] = {
                    "Stock": 0,
                    "Price": 0,
                    "cPrice": 0
                }

        json.dump(json_data, jsonFile, indent=4)
    
    ticker_lines = ticker_lines + 1

def get_net():
    net_val = []
    net = open('net.txt', "a")

    with open('sim.json', "r") as jsonFile:
        json_data = json.load(jsonFile)

    for i in json_data["Index"]:
        net_val.append(json_data['Index'][i]['Stock'] * json_data['Index'][i]['cPrice'])

    with open('sim.json', "w") as jsonFile:
        json_data['Net'] = sum(net_val) + json_data["Cash"]
        net.write(str(json_data['Net']) + "\n")
        json.dump(json_data, jsonFile, indent=4)
    net.close()

def current_price(data, json_data, temp, i):
    with open("sim.json", "w") as jsonFile:
        json_data['Index'][temp]['cPrice'] = data['Close'][i]
        json.dump(json_data, jsonFile, indent=4)

def buy_eq(data, json_data, temp, i):
    with open("sim.json", "w") as jsonFile:
        json_data['Index'][temp]['Stock'] = json_data['Index'][temp]['Stock'] + float((json_data['Cash']/float(ticker_lines))/data['Close'][i]) #simulating buying, with part shares #temp reffering to stock ticker diviide by amount of tickers in Ticker.txt
        json_data['Cash'] = json_data['Cash'] - (json_data['Cash']/ticker_lines)
        json_data['Index'][temp]['Price'] = data['Close'][i] #bought at what price

        #write to log file
        log.write("Bought : " + str(json_data['Index'][temp]['Stock']) + " " + str(data['Ticker'][i]) + " at : " + str(data['Close'][i]) + "\n") 
        json.dump(json_data, jsonFile, indent=4)

def sell_eq(data, json_data, temp, i, p): #p is percentage of shares sold
    with open("sim.json", "w") as jsonFile:                   
        if(json_data['Index'][temp]['Stock'] == 0): #log file formatting
            json_data['Cash'] = json_data['Cash']  + (json_data['Index'][temp]['Stock'] * data['Close'][i]) #simuilates selling
        else:
            log.write("Sold : " + str(json_data['Index'][temp]['Stock']) + " " + str(data['Ticker'][i]) + " at : " + str(data['Close'][i]) + "\n") 
            json_data['Cash'] = json_data['Cash'] + ((json_data['Index'][temp]['Stock'] * p) * data['Close'][i]) #simuilates selling, p = percentage of shares being sold
            json_data['Index'][temp]['Stock'] = (json_data['Index'][temp]['Stock'] - (json_data['Index'][temp]['Stock'] * p))
        json.dump(json_data, jsonFile, indent=4)

def main():
    ticker = open('Ticker.txt', "r")

    for u in ticker:
        temp = "" #formatting
        if(u[-1:] == "\n"): #formatting
            data = yf.download(u[:-1], group_by="Ticker", period='1d', interval='1m')
            data['Ticker'] = u[:-1]
            temp = u[:-1]
        else:
            data = yf.download(u, group_by="Ticker", period='1d', interval='1m')
            data['Ticker'] = u
            temp = u

        sum_lines = 0
        for j, i in enumerate(data['Ticker']):
            sum_lines = j

        def SMA5(j, x): #SMA start
            sum = 0
            for i in range(x):
                sum = sum + data['Close'][j-i]
            return sum/x

        sum_lines = 0
        for j, i in enumerate(data['Ticker']):
                    sum_lines = j

        SMA5_data = [0]
        SMA15_data = [0]
        for j in range(1, sum_lines+1):
            SMA5_data.append(SMA5(j, 2)) #SMA5 = 7
            SMA15_data.append(SMA5(j, 4)) #SMA15 #testing 20

        data['SMA5'] = SMA5_data 
        data['SMA15'] = SMA15_data #SMA ned

        trend = [0] #1 = pos, 0 = neg

        for i in range(1,sum_lines+1):
            trend.append(data['Close'][i]/((data['Close'][i-1])))

        data['Trend'] = trend #Adding trend to df

        def trade(i): #trade simulator
            with open('sim.json', "r") as jsonFile:
                json_data = json.load(jsonFile)

            current_price(data, json_data, temp, i)

            if(data['SMA5'][i-1] < data['SMA15'][i-1] and data['SMA5'][i] > data['SMA15'][i] and (data['SMA5'][i] - data['SMA15'][i]) >= 0.01): 
                #MA5t-1 < MA10t-1 || MA5t > MA10t || and (MA5t - MA10t) >= 0.01
                buy_eq(data, json_data, temp, i)

            else:
                if(trend[i-1] - trend[i] < 0): #sells almost perfect
                    sell_eq(data, json_data, temp, i, 1)
                        
                else: 
                    pass    #hold

  
        trade(len(data)-1)

    get_net()
    with open('sim.json', "r") as jsonFile:
        json_data = json.load(jsonFile)

    print("\nCash: ", json_data['Cash'], "\nNet: ", json_data['Net'], "\n")



json_file_formatting()
for i in range(600):
    main()
    print("\n------------------------", i, "\n")
    t.sleep(60) #sleeps for 5 min fo rprices to update
