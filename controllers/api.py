# coding: utf8

session.forget(response)
time_exp = IS_LOCAL and 3 or 66

import datetime
from decimal import Decimal

import db_common
import db_client
import serv_to_buy

def help():
    redirect(URL('index'))

@cache.action(time_expire=time_exp, cache_model=cache.disk) #, vars=False, public=True, lang=True)
def index():
    response.title = T('Как начать принимать оплаты биткоинами на сайте')
    response.meta['keywords']=T('оплты биткоинами, платежи биткоинами, приём биткоинов, скрипт биткоин сайта')
    response.meta['description']=T('Организуй приём биткоинов на своём сайте, скрипт биткоин сайта')
    #  http://127.0.0.1:90/ipay/clients/api/get_rate?curr_in=BTC&curr_out=RUB&vol_in=0.23
    # https://7pay.in/ipay/clients/api/get_rate?curr_in=RUB&curr_out=BTC&vol_in=230
    return dict()


@cache.action(time_expire=time_exp, cache_model=cache.disk, vars=True, public=True, lang=False)
def rates():
    import time
    time.sleep(1)
    if 'wp' in request.args:
        # это переделать имена параметров под http://web-payment.ru/ стандарт
        WPnames = request.args.index('wp')
        deal_sel = WPnames and request.args(0) or request.args(1)
        WPnames = True
    else:
        deal_sel = request.args(0)
        WPnames = False
        
    #print deal_sel
    if deal_sel and deal_sel.upper() == 'HELP':
        return 'rates/[deal] - deal = PH_7RUB | TO_YDRUB | IN_YDRUB | TO_COIN | None - all'
    import rates_lib, db_client, ed_common
    rub_curr, x, ecurr_out = db_common.get_currs_by_abbrev(db,"RUB")
    ecurr_out_id = ecurr_out.id
    vol_rub = 1000
    res = []
    currs_in_max = {}
    currs_to_max = {}
    dealer_deal = None
    to_abbrev = 'PH_7RUB'
    if not deal_sel or deal_sel.upper() == to_abbrev:
        ## сначала длля телефона
        if TO_PHONE7_ID:
            deal = db.deals[ TO_PHONE7_ID ]
        else:
            deal = db(db.deals.name=='phone +7').select().first()
        dealer, dealer_acc, dealer_deal = ed_common.select_ed_acc(db, deal, ecurr_out)
        #print deal.name, 'dealer:', dealer_deal
        to_max = round(float(db_common.get_balance_dealer_acc( dealer_acc )), 8)

        for r in db((db.currs.id==db.xcurrs.curr_id)
                          & (db.currs.used==True)).select():
            curr_in = r.currs
            # теперь курс и мзду нашу найдем
            pr_b, pr_s, rate = rates_lib.get_average_rate_bsa(db, curr_in.id, rub_curr.id, None)
            if not rate: continue
            vol_out = vol_rub # в рублях
            in_max = curr_in.max_bal or 0
            if in_max>0:
                bal = db_client.curr_free_bal(curr_in)
                in_max = round(float(in_max - bal), 8)
            in_abbrev = curr_in.abbrev
            currs_in_max[ in_abbrev ] = in_max

            is_order = True
            vol_in, tax_rep = db_client.calc_fees_back(db, deal, dealer_deal, curr_in, rub_curr, vol_out,
                                               rate, is_order, note=0)
            ##rate = vol_out_new / vol_in
            '''
            <rates>
                <item>
                <from>PMEUR</from>
                <to>PMUSD</to>
                <in>1</in>
                <out>1.07</out>
                <amount>4322.79649</amount>
                <param>manual</param>
                <minamount>0 EUR</minamount>
                </item>
            '''
            if WPnames:
                item = { 'from': in_abbrev, 'to': to_abbrev,
                       'in': round(float(vol_in),8 ), 'out': vol_out,
                       'amount': to_max }
            else:
                item = { 'in': in_abbrev, 'to': to_abbrev,
                       'in_vol': round(float(vol_in),8 ), 'to_vol': vol_out,
                       'to_max': to_max }
            if in_max: item['in_max'] = in_max
            res.append(item)
    ###############
    ## теперь на ЯД кошелек
    to_abbrev = 'YDRUB'
    if not deal_sel or deal_sel.upper() == 'TO_YDRUB':
        if TO_WALLET_ID:
            deal = db.deals[ TO_WALLET_ID ]
        else:
            deal = db(db.deals.name=='BUY').select().first()
        dealer, dealer_acc, dealer_deal = ed_common.select_ed_acc(db, deal, ecurr_out)
        #print deal.name, 'dealer:', dealer_deal
        to_max = dealer_max = round(float(db_common.get_balance_dealer_acc( dealer_acc )), 8)
        for r in db((db.currs.id==db.xcurrs.curr_id)
                          & (db.currs.used==True)).select():
            curr_in = r.currs
            # теперь курс и мзду нашу найдем
            pr_b, pr_s, rate = rates_lib.get_average_rate_bsa(db, curr_in.id, rub_curr.id, None)
            if not rate: continue

            vol_out = vol_rub # в рублях
            is_order = True
            vol_in, tax_rep = db_client.calc_fees_back(db, deal, dealer_deal, curr_in, rub_curr, vol_out,
                                               rate, is_order, note=0)
            in_abbrev =  curr_in.abbrev
            if WPnames:
                item = { 'from': in_abbrev, 'to': to_abbrev,
                       'in': round(float(vol_in),8 ), 'out': vol_out,
                       'amount': to_max }
            else:
                item = { 'in': in_abbrev, 'to': to_abbrev,
                       'in_vol': round(float(vol_in),8 ), 'to_vol': vol_out,
                       'to_max': to_max }
            ## вытащим из кеша если он там есть
            in_max = currs_in_max.get( in_abbrev )
            if in_max == None:
                in_max = curr_in.max_bal or 0
                if in_max>0:
                    bal = db_client.curr_free_bal(curr_in)
                    in_max = round(float(in_max - bal), 8)
            if in_max: item['in_max'] = in_max
            res.append(item)

        ###### покупка через ЯДеньги
    if not deal_sel or deal_sel.upper() == 'IN_YDRUB':
        in_abbrev = 'YDRUB'
        if TO_BUY_ID:
            deal = db.deals[ TO_BUY_ID ]
        else:
            deal = db(db.deals.name=='BUY').select().first()
        # тут пустой %% dealer, dealer_acc, dealer_deal = ed_common.select_ed_acc(db, deal, ecurr_out)
        #print deal.name, 'dealer:', dealer_deal
        dealer_deal = None
        in_max = 57000 # у фиатного диллера одну покупку ограничим
        for r in db((db.currs.id==db.xcurrs.curr_id)
                          & (db.currs.used==True)).select():
            curr_out = r.currs
            vol_in = vol_rub # в рублях
            to_abbrev = curr_out.abbrev
            currs_to_max[ to_abbrev ] = to_max = round(float(db_client.curr_free_bal(curr_out)), 8)

            # теперь курс и мзду нашу найдем
            pr_b, pr_s, rate = rates_lib.get_average_rate_bsa(db, rub_curr.id, curr_out.id, None)
            if not rate: continue
            is_order = True
            vol_out, tax_rep = db_client.calc_fees(db, deal, dealer_deal, rub_curr, curr_out, vol_in,
                                               rate, is_order, note=0)
            if WPnames:
                item = { 'from': in_abbrev, 'to': to_abbrev,
                       'in': vol_in, 'out': round(float(vol_out),8 ),
                       'amount': to_max, 'in_max': in_max  }
            else:
                item = { 'in': in_abbrev, 'to': to_abbrev,
                       'in_vol': vol_in, 'to_vol': round(float(vol_out),8 ),
                       'to_max': to_max, 'in_max': in_max }
            res.append(item)

    #########
    # обмен крипты
    if not deal_sel or deal_sel.upper() == 'TO_COIN':
        if TO_COIN_ID:
            deal = db.deals[ TO_COIN_ID ]
        else:
            deal = db(db.deals.name=='to COIN').select().first()
        for r_in in db((db.currs.id==db.xcurrs.curr_id)
                          & (db.currs.used==True)).select():
            curr_in = r_in.currs
            in_abbrev = curr_in.abbrev
            vol_in = vol_rub * rates_lib.get_avr_rate_or_null(db, rub_curr.id, curr_in.id)
            in_max = currs_in_max.get( in_abbrev )
            if in_max == None:
                in_max = curr_in.max_bal or 0
                if in_max>0:
                    bal = db_client.curr_free_bal(curr_in)
                    in_max = round(float(in_max - bal), 8)
            #print curr_in.abbrev, ' to RUB', vol_in
            for r_out in db((db.currs.id==db.xcurrs.curr_id)
                              & (db.currs.used==True)).select():
                curr_out = r_out.currs
                if curr_in.id == curr_out.id: continue
                # теперь курс и мзду нашу найдем
                pr_b, pr_s, rate = rates_lib.get_average_rate_bsa(db, curr_in.id, curr_out.id, None)
                if not rate: continue

                to_abbrev = curr_out.abbrev
                to_max = currs_to_max.get(to_abbrev, round(float(db_client.curr_free_bal(curr_out)), 8))
                # для каждого направление - свое дело

                is_order = True
                vol_out, tax_rep = db_client.calc_fees(db, deal, dealer_deal, curr_in, curr_out, vol_in,
                                                   rate, is_order, note=0)
            if WPnames:
                item = { 'from': in_abbrev, 'to': to_abbrev,
                       'in':round(float(vol_in),8), 'out': round(float(vol_out),8),
                       'amount': to_max }
            else:
                item = { 'in': in_abbrev, 'to': to_abbrev,
                           'in_vol':round(float(vol_in),8), 'to_vol': round(float(vol_out),8),
                           'to_max': to_max }
                if in_max: item['in_max'] = in_max
                res.append(item)
    return request.extension == 'html' and dict(
        h=DIV(BEAUTIFY({'rates': res}), _class='container')) or {'rates': res}


@cache.action(time_expire=time_exp, cache_model=cache.disk, vars=True, public=True, lang=True)
def curr_get_info():
    import time
    time.sleep(1)

    curr_abbrev = request.args(0)
    if not curr_abbrev:
        return {"error": "empty curr - example: curr_get_info/btc" }
    curr_abbrev = curr_abbrev.upper()
    from db_common import get_currs_by_abbrev
    curr,xcurr,e = get_currs_by_abbrev(db, curr_abbrev)
    if not xcurr:
        return {"error": "invalid curr: " + curr_abbrev }
    from crypto_client import conn
    try:
        conn = conn(curr, xcurr)
    except:
        conn = None
    if not conn:
        return {'error': 'Connection to ' + curr_abbrev + ' wallet is lost. Try later'}
    print conn
    try:
        res = conn.getinfo()
    #except Exception as e:
    except Exception, e:
        return {'error': 'Connection to ' + curr_abbrev + ' wallet raise error [%s]. Try later' % e}
    
    return res

# http://127.0.0.1:8000/shop/api/validate_addr.json/14qZ3c9WGGBZrftMUhDTnrQMzwafYwNiLt
def validate_addr():
    import time
    time.sleep(1)
    addr = len(request.args)>0 and request.args[0] or request.vars.get('addr')
    if not addr:
        return {'error':"need addr: /validate_addr.json/[addr]"}
    from db_common import get_currs_by_addr
    curr, xcurr, _ = get_currs_by_addr(db, addr)
    if not xcurr:
        return {"error": "invalid curr"}
    from crypto_client import conn
    conn = conn(curr, xcurr)
    if not conn:
        return {"error": "not connected to wallet [%s]" % curr.abbrev}
    valid = conn.validateaddress(addr)
    if not valid.get('isvalid'):
        return {"error": "invalid for [%s]" % curr.abbrev}
    return { 'curr': curr.abbrev, 'ismine': valid.get('ismine') }

@cache.action(time_expire=time_exp*10, cache_model=cache.disk)
def get_rates():
    session.forget(response)
    return { 'error': 'please use /rates/to_ydrub or rates/help API call instead'}

@cache.action(time_expire=time_exp*10, cache_model=cache.disk)
def get_buy_rates():
    session.forget(response)
    return { 'error': 'please use /rates/in_ydrub or rates/help API call instead'}
