#Function defenitions for putting csv data into ml-prediction formats

import pandas as pd
import numpy as np
from sklearn.linear_model import Ridge
from sklearn.preprocessing import MinMaxScaler

# create a differenced series
def difference(dataset, interval=1):
    diff = list()
    for i in range(interval, len(dataset)):
        value = dataset[i] - dataset[i - interval]
        diff.append(value)
    return pd.Series(diff)

def diff_scale(series):
    # extract raw values
    raw_values = series.values.reshape(-1,1)
    # transform data to be stationary
    diff_series = difference(raw_values, 1)
    diff_values = diff_series.values
    diff_values = diff_values.reshape(len(diff_values), 1)
    # rescale values to -1, 1
    scaler = MinMaxScaler(feature_range=(-1, 1))
    scaled_values = scaler.fit_transform(diff_values)
    scaled_values = scaled_values.reshape(len(scaled_values), 1)
    return scaler, scaled_values

def forecast_lstm(model, X, n_batch):
    # reshape input pattern to [samples, timesteps, features]
    X = X.reshape(1, 1, len(X))
    # make forecast
    forecast = model.predict(X, batch_size=n_batch)
    # convert to array
    return [x for x in forecast[0, :]]

def inverse_difference(history, yhat, interval=1):
    for j in range(1,len(yhat)+1):
        yhat[0][j] += yhat[0][j-1]
    ans = yhat+history
    return ans

def inverse_transform(last_val, forecast, scaler):
    # create array from forecast
    forecast = np.array(forecast)
    forecast = forecast.reshape(1, len(forecast))
    # invert scaling
    inv_scale = scaler.inverse_transform(forecast)
    # store
    undiffed = inverse_difference(last_val,inv_scale)
    return undiffed

def series_to_supervised(data, n_in=1, n_out=1, dropnan=True):
    #Creates dataframe of supervised data X for n_in days and n_out days forward
    n_vars = 1 if type(data) is list else data.shape[1]
    df = pd.DataFrame(data)
    cols, names = list(), list()
    # input sequence (t-n, ... t-1)
    for i in range(n_in, 0, -1):
        cols.append(df.shift(i))
        names += [('var%d(t-%d)' % (j+1, i)) for j in range(n_vars)]
    # forecast sequence (t, t+1, ... t+n)
    for i in range(0, n_out):
        cols.append(df.shift(-i))
        if i == 0:
            names += [('var%d(t)' % (j+1)) for j in range(n_vars)]
        else:
            names += [('var%d(t+%d)' % (j+1, i)) for j in range(n_vars)]
    # put it all together
    agg = pd.concat(cols, axis=1)
    agg.columns = names
    # drop rows with NaN values
    if dropnan:
        agg.dropna(inplace=True)
    return agg

def prepare_data(series, n_test, n_lag, n_seq):
    # extract raw values
    raw_values = series.values.reshape(-1,1)
    # transform into supervised learning problem X, y
    supervised = series_to_supervised(raw_values, n_lag, n_seq)
    supervised_values = supervised.values
    # split into train and test sets
    train, test = supervised_values[0:-n_test], supervised_values[-n_test:]
    return train, test

def getRidgePred(dataset,n_test,n_lag,n_seq):
    train, test = prepare_data(dataset,n_test, n_lag, n_seq)
    Train_All = np.concatenate((train,test))

    # reshape training into [samples, timesteps, features]
    X, y = Train_All[:, 0:n_lag], Train_All[:, n_lag:]

    model = Ridge(alpha=1)
    model.fit(X,y.reshape(-1,n_seq))

    Future = model.predict(dataset[-n_lag:].values.reshape(1,30))[0]
    Future = np.append(dataset[-1],Future)
    #for i in range(len(Future)):
    f_list = [[dataset.index[-1] +
               pd.tseries.offsets.DateOffset(i),Future[i]] for i in range(0,n_seq+1)]

    df_fut = pd.DataFrame(data = f_list, columns=['Date','Price'])
    df_fut = df_fut.set_index('Date')
    return df_fut