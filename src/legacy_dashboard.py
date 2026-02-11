# -*- coding: utf-8 -*-
"""
Created on Fri Jul 22 11:11:28 2022

@author: Jack Vance
"""
####
# Stock Overview Dashboard
####

# Runs on plotly.dash

# input ticker (dropdown) and year(s)/TTM (multiselector - averaging) to view (IMO) most relevant info

# imports
import datetime as dt
import pandas as pd 

# dash components
import dash
from dash import html
from dash import dcc
from dash.dependencies import Input, Output, State
import plotly.express as px
import plotly.graph_objects as go
import plotly.io as pio
from plotly.subplots import make_subplots

# yfinance to grab stock data
import yfinance as yf

#plot templates to change style for all, including html
template_base = 'plotly_dark'
pio.templates['buffalo_stone'] = pio.templates[template_base]

pio.templates['buffalo_stone'].layout['paper_bgcolor'] = '#696969'
pio.templates['buffalo_stone'].layout['plot_bgcolor'] = '#696969'
pio.templates['buffalo_stone'].layout['xaxis']['gridcolor'] = '#696969'
pio.templates['buffalo_stone'].layout['yaxis']['gridcolor'] = '#696969'
pio.templates['buffalo_stone'].layout['yaxis']['zerolinecolor'] = '#ffffff'

template = 'buffalo_stone' 

pio.templates.default = template

#pio.templates['buffalo_stone'].layout
#pio.templates['buffalo_stone'].layout
#pio.templates['buffalo_stone'].layout

#pio.templates.default['paper_bgcolor'] = "#696969"

text_color = pio.templates[template].layout['font']['color']
bg_color = pio.templates[template].layout['paper_bgcolor']
#bg_color = "#696969"

#define functions for later use - simplifies calls later, might speed reruns slightly
def getData(ticker, year_range): #all data pulling functions
    # price chart from pdr
    display_start = str(year_range[0])+'-1-1'
    
    if year_range[1] == dt.date.today().year:
        display_end = dt.date.today()
    else:
        display_end = str(year_range[1])+'-12-31'
        
       # Extended date range for moving average calculation
    # Add ~300 trading days (about 1.5 years) before display start to ensure we have enough data for 200-day MA
    display_start_date = dt.datetime.strptime(display_start, '%Y-%m-%d').date()
    extended_start_date = display_start_date - dt.timedelta(days=400)  # Extra buffer
    extended_start = extended_start_date.strftime('%Y-%m-%d')
    
    print(f"Fetching extended data from {extended_start} to {display_end}")
    print(f"Display window: {display_start} to {display_end}")
    
    # Fetch extended price data for moving averages
    prices_extended = yf.download(ticker, extended_start, display_end)
    if prices_extended.columns.nlevels > 1:
        prices_extended.columns = prices_extended.columns.droplevel(1)
    
    # Filter to display window for final output
    prices = prices_extended[display_start:str(display_end)]
    
    # Calculate moving averages on extended data
    ma50_extended = prices_extended['Close'].rolling(50).mean()
    ma200_extended = prices_extended['Close'].rolling(200).mean()
    
    # Filter moving averages to display window
    ma50 = ma50_extended[display_start:str(display_end)]
    ma200 = ma200_extended[display_start:str(display_end)]
    
    # Add moving averages as columns to the display dataframe
    prices = prices.copy()
    prices['MA50'] = ma50
    prices['MA200'] = ma200
    
    # everything else from yf
    tick = yf.Ticker(ticker)
    
    #general stock info
    info = tick.info
    
    #tick.financials
    reduced_financials_keys = ['Total Revenue',
                              'Operating Expense',
                              'Cost Of Revenue',
                              'Operating Income',
                              'Net Income',
                              'Research And Development'                       
                              ]
    rf_keys = []
    for key in reduced_financials_keys:
        if key in tick.financials.index:
            rf_keys.append(key)
    reduced_financials = tick.financials.transpose()[rf_keys]
    
    #tick.major_holders 
    
    #tick.balance_sheet
    balance_sheet = tick.balance_sheet.transpose()
 
    #tick.cashflow #not used, could be
    
    #tick.earnings #not used, could be
    
    return prices, info, reduced_financials, balance_sheet
    

def priceChart(info, prices): #price chart function - top dead center
    fig = make_subplots(
            rows=2, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.1,
            row_heights=[0.75, 0.25]  # Price chart gets 75%, volume gets 25%
        )    

    ma50 = prices['MA50']
    ma200 = prices['MA200']
    
    # Add price traces to top subplot
    fig.add_trace(
        go.Scatter(
            x=prices.index,
            y=prices['Close'],
            name='Close Price',
            marker={'color':'#ffffff', 'size':2},
            mode='markers'), row=1, col=1)
    fig.add_trace(
        go.Scatter(
            x=prices.index,
            y=ma50,
            name='50-day Moving Average'), row=1, col=1)
    fig.add_trace(
        go.Scatter(
            x=prices.index,
            y=ma200,
            name='200-day Moving Average'), row=1, col=1)
            
    if 'Volume' in prices.columns:
        # Calculate colors based on daily price change
        colors = []
        for i in range(len(prices)):
            if i == 0:
                colors.append('#83B0D6')  # Neutral for first day
            else:
                # Compare today's close to yesterday's close
                if prices['Close'].iloc[i] > prices['Close'].iloc[i-1]:
                    colors.append('#00CC96')  # Green for up days
                else:
                    colors.append('#FF6692')  # Red for down days
        
        fig.add_trace(go.Bar(
            x=prices.index,
            y=prices['Volume'],
            name='Daily Volume',
            marker_color=colors,
            showlegend=False), row=2, col=1)
    
    fig.update_layout(
        yaxis_title='Close Price (USD)',
        title='%s (%s)'%(info['shortName'], info['symbol']),
        yaxis2_title='Volume',
        xaxis2_title='Date')

    return fig

def financialsTimeline(reduced_financials): #row 2, left side
    fin_plot = px.line(
        reduced_financials, 
        x=reduced_financials.index, 
        y=reduced_financials.columns,
        title = 'Recent Annual Cashflows',
        color_discrete_sequence = ['#ffffff', '#DE3B3E', '#EC6C5B', '#B2C7AD', '#00CC96', '#83B0D6']
    )
    fin_plot.update_traces(hovertemplate='%{y} <br> %{x}')
    fin_plot.update_layout(xaxis_title='Date', 
                           yaxis_title='USD',
                           legend_title="")
    return fin_plot

def printInfo(info): #row two, right side
    # lots of info to pick from, what do you want?
    name = info['longName']
    #snam = info['shortName']
    summ = info['longBusinessSummary']+" "#[0:1253] (1226/META, 1076/GOOG)
    web = info['website']
    ind = info['industry']
    sect = info['sector']
    price = info['currentPrice']
    fpe = info['forwardPE']
    tpe = info['trailingPE']
    #fte = into['fullTimeEmployees']
    cap = info['marketCap']
    #rec = info['recommendationKey']
    #tplow = info['targetLowPrice']
    #tpavg = info['targetMeanPrice']
    #tpmid = info['targetMedianPrice']
    #tphigh = info['targetHighPrice']
    #peg = 
    try:
        ebitda = info['ebitda'] #earnings before interest, tax, depreciation, amoritization
    except:
        ebitda = "N/A"
    #dte = info['debtToEquity']
    #spe = #shiller pe (standardized w/ inflation)
    try:
        debitda = info['totalDebt'] / ebitda #debt to ebitda
    except:
        debitda = "N/A"
    
    text = (f'{name}    {web}'+'\n',
            f'Sector: {sect};    Industry: {ind}'+'\n',
            f'Current Price per Share: ${price};    Market Capitalization: ${cap:,.0f}'+'\n',
            f'Trailing P/E: {tpe:.2f};    Forward P/E: {fpe:.2f}'+'\n',
            f'Debt to EBITDA Ratio: {debitda:.3}'+'\n',
            f'{summ}'+'\n')
    return text
    
    
def balanceSheetPlots(balance_sheet): # could be two separate functions
    #Assets v Liab bar chart - 3rd row, left
    x = ['Total Assets', 'Total Liabilities Net Minority Interest']
    #y's to seperate btwn current/non
    flag = False
    try:
        y_cur = balance_sheet[['Current Assets', 'Current Liabilities']].iloc[0]
    except:
        flag = True
    try:
        y_nc = balance_sheet[['Total Non Current Assets', 'Total Non Current Liabilities Net Minority Interest']].iloc[0]
    except:
        flag = True
        
    colors = ['#1f77b4', '#ff7f0e'] # considering using custom color scheme here 

    if flag!=True:
        bs_bar = go.Figure(data=[
            go.Bar( #remove for total
                name='Non-Current',
                x=x,
                y=y_nc,
                marker_color=['#83B0D6','#EC6C5B'],
                #marker_color=colors[0], #
                hovertemplate = '<b>Non-Current:</b> $%{y:,.0f},<extra></extra>'),
            go.Bar(
                name ='Current',
                x=x, 
                y=y_cur, 
                marker_color=['#4A85BE','#DE3B3E'], #
                hovertemplate= '<b>Current:</b> $%{y:,.0f},<extra></extra>')
            ])
    else:
        bs_bar = go.Figure(data=[
            go.Bar(
                x=x,
                y=balance_sheet[x].iloc[0],
                marker_color=['#669aca', '#e5544c'])
            ])
    bs_bar.update_layout(
        barmode='group', # remove for total
        title='Assets vs Liabilities',
        yaxis={'title': 'USD'},
        showlegend=False
        )
    
    # sunburst: Balance Sheet Breakdown - row 3 right
    # yf doesn't return same set for every ticker. Need to account for missing outputs.
    labels = []
    parents = []
    parent_dict={'Total Assets':'', 
                     'Current Assets':'Total Assets', 
                         'Inventory':'Current Assets', 
                         'Receivables':'Current Assets', 
                         'Cash And Cash Equivalents':'Current Assets',
                         'Other Short Term Investments':'Current Assets',
                         'Other Current Assets':'Current Assets',
                     'Total Non Current Assets':'Total Assets',
                         'Net PPE':'Total Non Current Assets',
                         'Investments And Advances':'Total Non Current Assets',
                         'Goodwill And Other Intangible Assets':'Total Non Current Assets',
                         'Other Non Current Assets':'Total Non Current Assets',
                 'Total Liabilities Net Minority Interest':'',
                     'Current Liabilities':'Total Liabilities Net Minority Interest',
                         'Payables And Accrued Expenses':'Current Liabilities',
                         'Current Deferred Liabilities':'Current Liabilities',
                         'Current Debt And Capital Lease Obligation':'Current Liabilities',
                         'Other Current Liabilities':'Current Liabilities',
                     'Total Non Current Liabilities Net Minority Interest':'Total Liabilities Net Minority Interest',
                         'Long Term Debt And Capital Lease Obligation':'Total Non Current Liabilities Net Minority Interest',
                         'Other Non Current Liabilities':'Total Non Current Liabilities Net Minority Interest'}
    
    #create labels/parents according to dict and data
    for key in parent_dict.keys():
        if key in balance_sheet.columns:  
            labels.append(key)
            parents.append(parent_dict[key])
    
    #build color chart based on label values 
    colors=[]
    for label in labels:
        if label=='Current Assets':
            colors.append('#4A85BE')
        elif label=='Total Non Current Assets':
            colors.append('#83B0D6')
        elif label=='Current Liabilities':
            colors.append('#DE3B3E')
        elif label=='Total Non Current Liabilities Net Minority Interest':
            colors.append('#EC6C5B')
        elif label=='Total Assets':
            colors.append('#669aca ')
        elif label=='Total Liabilities Net Minority Interest':
            colors.append('#e5544c')
        else:
            colors.append('#ffffff')
            
    #finish color chart based on parent values (less typing this way)
    for i, parent in enumerate(parents):
        if parent=='Current Assets':
            colors[i]=('#4A85BE')
        elif parent=='Total Non Current Assets':
            colors[i]=('#83B0D6')
        elif parent=='Current Liabilities':
            colors[i]=('#DE3B3E')
        elif parent=='Total Non Current Liabilities Net Minority Interest':
            colors[i]=('#EC6C5B')
            
    #create sunburst
    bs_sunburst = go.Figure(go.Sunburst(
        labels=labels,
        parents=parents,
        values=balance_sheet[labels].iloc[0],
        branchvalues='total',
        hovertemplate='%{label} <br> $%{value:,.0f}<extra></extra>',
        marker={'colors':colors}
        #color_discrete_map={'(?)':'black', 'Total Assets':'gold', 'Total Liab':'darkblue'}
    ))

    bs_sunburst.update_layout(
        title='Balance Sheet Breakdown',
        margin = dict(r=0, b=10, t=50, l=50)
        )
    return bs_bar, bs_sunburst

#create dash app
app = dash.Dash(__name__, title='Buy-Son Stock Evaluator')

#create html layout
app.layout = html.Div(children=[html.Div(children=[html.A("Big Ol' Buffalo Detector",
                                                          href='http://bigolbuffalo.com/'),
                                                   html.A('Enter the Bison',
                                                          href='http://bigolbuffalo.com/EnterTheBison.html'),
                                                   html.A('Buffalo Bark Machine',
                                                          href='http://bigolbuffalo.com/BuffaloBarkMachine.html'),
                                                   html.A('Bython Projects',
                                                          href='http://bigolbuffalo.com/Bython.html')],
                                         className='topnav'),
                      
                                html.Div(children=[html.H1('Buy-Son (Stock Evaluation Dashboard)',
                                                  style={'textAlign': 'center',
                                                         'fontSize': 32}),
                                          html.H2('~10s to retrieve new data',
                                                  style={'textAlign': 'center',
                                                         'fontSize': 16}),
                                          
                                          html.P('Select a company from the dropdown list, or enter your own ticker symbol.'),
                                          html.P('The year range slider only applies to the price chart. Data from financial reports is always for the past 3 years (the maximum provided by Yahoo Finance).'),
                                          
                                          html.H3('Company:'),
                                          
                                          dcc.Dropdown(id='company-dropdown', 
                                                       options=[
                                                          {'label': 'Apple : AAPL', 'value': 'AAPL'},
                                                          {'label': 'Microsoft : MSFT', 'value': 'MSFT'},
                                                          {'label': 'Alphabet (CLass A) : GOOGL', 'value': 'GOOGL'},
                                                          {'label': 'Alphabet (Class C) : GOOG', 'value': 'GOOG'},
                                                          {'label': 'Amazon : AMZN', 'value': 'AMZN'},
                                                          {'label': 'Tesla : TSLA', 'value': 'TSLA'},
                                                          {'label': 'Berkshire Hathaway (Class B) : BRK-B', 'value': 'BRK-B'},
                                                          {'label': 'NVIDIA : NVDA', 'value': 'NVDA'},
                                                          {'label': 'Meta (Class A) : META', 'value': 'META'},
                                                          {'label': 'UnitedHealth : UNH', 'value': 'UNH'},
                                                          {'label': 'Visa : V', 'value': 'V'},
                                                          {'label': 'Johnson & Johnson : JNJ', 'value': 'JNJ'},
                                                          {'label': 'Walmart : WMT', 'value': 'WMT'},
                                                          {'label': 'JPMorgan Chase & Co. : JPM', 'value': 'JPM'},
                                                          {'label': 'The Procter & Gamble Company : PG', 'value': 'PG'},
                                                          {'label': 'Mastercard Incorporated : MA', 'value': 'MA'},
                                                          {'label': 'Bank of America Corporation : BAC', 'value': 'BAC'},
                                                          {'label': 'Exxon Mobil Corporation : XOM', 'value': 'XOM'},
                                                          {'label': 'The Home Depot : HD', 'value': 'HD'},
                                                          {'label': 'Chevron Corporation : CVX', 'value': 'CVX'}
                                                          ],
                                                       value='AAPL',
                                                       placeholder='no selection',
                                                       searchable=True,
                                                       style={'width': '50%', 'color':'#111111'}
                                                       ),     
                                          
                                          #custom ticker input/button
                                          dcc.Input(id='custom-ticker',
                                                    value='',
                                                    style={'width':'5%'}),
                                          html.Button('Add Symbol & Run', id='button', n_clicks=0),
                                          ###
                                          
                                          html.Br(),
                                          
                                          html.H3('Year(s):'),
                                          
                                          dcc.RangeSlider(id='year-slider', 
                                                          min=dt.date.today().year-20, max=dt.date.today().year, step=1,
                                                          marks={int(n) : {'label' : str(n), 'style':{'color':'#ffffff'}} for n in range(dt.date.today().year-20, dt.date.today().year)},
                                                          value=[dt.date.today().year-3, dt.date.today().year]
                                                          ),
                                          
                                          html.Br(),
                                          
                                          html.Div(dcc.Graph(id='historical-close-price-chart')),
                                          
                                          html.Div(children=(
                                              html.Div(dcc.Graph(id='historical-financials-chart')),
                                              dcc.Markdown(id='info-text', 
                                                           style={'breakInside':'avoid-column'})
                                              ),
                                              style={'columnCount':2,
                                                     'columnGap':'0px'}
                                              ),
                                              
                                          html.Div(children=(
                                              html.Div(dcc.Graph(id='balance-sheet-bar-chart')),
                                              html.Div(dcc.Graph(id='balance-sheet-sunburst-chart'))
                                              ),
                                              style={'columnCount':2, 'columnGap':'0px', 'marginBottom':25}
                                          ),
                                          
                                          html.Br(),
                                          
                                          html.Hr(),
                                          
                                          html.Br(),
                                          
                                          html.Div(children=(
                                              html.P('This dashboard is designed around a "value investing" strategy. How does the price relate to the current and anticipated future earnings of a company?'),
                                              html.P('Looking at these charts, you should be able to get some idea of the recent earnings trajectory of a company, its potential for financial improvement and stability, and the relative price.'),
                                              html.P('Central to this analysis is the "price-to-earnings" ratio, or P/E, which is the price per dollar of annual earnings currently offered by the stock. A PE of 1 means that your share would "earn" (though not paid to YOU) its value each year. A PE of 10 means it would earn a 100% ROI in 10 years, and so on. Of course, this must be weighed against future expectations for the company. A PE of 100 may be justified if the company can be expected to dramatically increase (~10x) earnings in the near future.'),
                                              ),
                                              style={'textAlign':'center'}
                                              ),
                                          
                                          html.Br(),
                                          
                                          html.H3('Notable Terms and Definitions:'),
                                          dcc.Markdown('***Trailing P/E:*** The price-to-earnings ratio calculated based on actual earnings over the past 12 months reported by the company.'),
                                          dcc.Markdown('***Forward P/E:*** The price-to-earnings ratio calculated based on anticipated future earnings reported by the company.'),
                                          dcc.Markdown('***EBITDA:*** Earnings before interest, taxes, depreciation, and amortization'),
                                          dcc.Markdown('***Cost of Revenue:*** Total cost of manufacturing and delivering a product or service to consumers. Used as a theoretical minimum for Total Operating expenses.'),
                                          dcc.Markdown('***Operating Income:*** Equivalent to Total Revenue minus Total Operating Expenses. Does NOT account for interest, taxes, or non-recurring expenses (e.g., lawsuits).'),
                                          
                                          html.Br(),
                                          
                                          html.A('Source Code', href='http://bigolbuffalo.com/Buy-Son-Source.txt', style={'fontStyle':'italic'})
                                          ],
                                          style={'color':f'{text_color}',
                                                 'backgroundColor':f'{bg_color}',
                                                 'padding':10,
                                                 'paddingTop':50})
                                ])

#callback function for getting data and building plots
@app.callback([Output(component_id='historical-close-price-chart', component_property='figure'),
              Output(component_id='historical-financials-chart', component_property='figure'),
              Output(component_id='info-text', component_property='children'),
              Output(component_id='balance-sheet-bar-chart', component_property='figure'),
              Output(component_id='balance-sheet-sunburst-chart', component_property='figure')],
              [Input(component_id='company-dropdown', component_property='value'),
               Input(component_id='year-slider', component_property='value')])

def everything(ticker, year_range):
    try:
        print(f"Fetching data for {ticker} from {year_range}") # Debug print
        prices, info, reduced_financials, balance_sheet = getData(ticker, year_range)
    
        if prices.empty:
            print(f"No price data for {ticker}")
            
        price_chart = priceChart(info, prices)
        financials_chart = financialsTimeline(reduced_financials)
        text = printInfo(info)
        bs_bar, bs_sunburst = balanceSheetPlots(balance_sheet)
        
        return price_chart, financials_chart, text, bs_bar, bs_sunburst
    
    except Exception as e:
        print(f"Error in everything function: {e}")
        # Return empty charts instead of crashing
        empty_fig = go.Figure()
        empty_fig.add_annotation(text=f"Error loading data: {str(e)}", 
                               xref="paper", yref="paper", x=0.5, y=0.5)
        return empty_fig, empty_fig, f"Error: {str(e)}", empty_fig, empty_fig

#callback function to add new ticker to list (consequently runs plots)
@app.callback(
    [Output(component_id='company-dropdown', component_property='value'),
    Output(component_id='company-dropdown', component_property='options')],
    [Input(component_id='button', component_property='n_clicks'),
     Input(component_id='company-dropdown', component_property='options')],
    State(component_id='custom-ticker', component_property='value')
    )

def altTick(click, pick, tick): # too. much. fun.
#click=n_clicks, pick='options' picklist, tick=new ticker symbol
    if tick == '':
        tick='AAPL'
    if click > 0:
        if tick not in [dic['value'] for dic in pick]:
            #name = yf.Ticker(tick).info['shortName'] #cool idea but takes too long
            pick.append({'label': tick, 'value': tick})
    return tick, pick

#run
if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8050, debug=True)
    
    #app.run(host='0.0.0.0', port=8050)