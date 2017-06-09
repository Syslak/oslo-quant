import argparse
from datetime import datetime, timedelta
from tabulate import tabulate

from markets import get_instrument
from historical_return_from_to_date import historical_return_from_to_date

def historical_return_dates(instrument, days_between):
    """"
    Find the historically best dates to buy and sell
    
    Args:
        instrument (markets.Instrument): Instrument to use in check
        days_between (int): Approximate number of days between buy and sell

    Return:
        dict with two lists sorted on average gain ratio
        and change of positive gain ratio:

            {'avg_gain_ratio': 
                [(buy_date, sell_date, avg_gain_ratio, pos_gain_ratio),..],
             'pos_gain':
                [(buy_date, sell_date, avg_gain_ratio, pos_gain_ratio),..]}
    """
    year = 2017
    date = datetime(year, 1, 1)

    results = []
    
    # loop through all the days in one year
    while date.year == year:

        buy_date = date
        sell_date = buy_date + timedelta(days=days_between)

        d = historical_return_from_to_date(instrument, buy_date, sell_date)

        results.append((buy_date,
                        sell_date,
                        d['avg_gain_ratio'], d['pos_gain_ratio']))
        
        date += timedelta(days=1)

    # sort by column a, then by column b
    avg_gain_list = sorted(results, key=lambda x: (x[2], x[3]), reverse=True)
    pos_gain_list = sorted(results, key=lambda x: (x[3], x[2]), reverse=True)
    
    d = {'avg_gain_ratio': avg_gain_list,
         'pos_gain_ratio': pos_gain_list}
    
    return d

def _print(results):
    """Print a tabulated list"""

    tab_list = []

    decimals = 4

    for r in results:
        tab_list.append((r[0].strftime("%Y-%m-%d"),
                         r[1].strftime("%Y-%m-%d"),
                         str(round(r[2], decimals)),
                         str(round(r[3], decimals))))

    print(tabulate(tab_list, headers=("Buy date",
                                      "Sell date",
                                      "Avg. gain ratio",
                                      "Pos. gain ratio")))

if __name__ == "__main__":
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Find the best dates to buy an sell")
    parser.add_argument("instrument", help="Instrument name (ex.: OBX)")
    parser.add_argument("days_between", type=int, help="Days between buy and sell")
    parser.add_argument("--avg_gain",
                        action='store_true',
                        help="Sorted by average gain ratio per year")
    parser.add_argument("--pos_gain",
                        action='store_true',
                        help="Sorted by number of years with positive gain")
    parser.add_argument("--worst",
                        action="store_true",
                        help="Find the worst dates instead of the best dates")
    parser.add_argument("--topn",
                        metavar="N",
                        type=int,
                        default=-1,
                        help="Show the top N entires only")
    args = parser.parse_args()
    
    # get the instrument from the database
    instrument = get_instrument(args.instrument.upper())

    # run the algorithm
    res = historical_return_dates(instrument, args.days_between)
    
    if args.avg_gain:
        l = res['avg_gain_ratio']
        
        if args.worst:
            l.reverse()
            print("\nWorst dates sorted by average gain")
        else:
            print("\nBest dates sorted by average gain")
            
        _print(l[:args.topn -1])
            
    if args.pos_gain:
        l = res['pos_gain_ratio']
        
        if args.worst:
            l.reverse()
            print("\nWorst dates sorted by change of positive gain gain")
        else:
            print("\nBest dates sorted by change of positive gain gain")
            
        _print(l[:args.topn -1])