import requests
from bs4 import BeautifulSoup
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

import pandas as pd

class ScrapingDOU:
    def __init__(self):
        self.driver = self.__getChromeDriver()

    def run(self,keywords:dict = {}, n_pages:int=1):
        #keywords2search = list(keywords.keys())
        #keywords2rmv = list(keywords.values())
        #print(keywords2rmv)

        dfinal = pd.DataFrame()
        for keys, vals_list in keywords.items():
            if n_pages == 1:
                #nesse caso é invertido, currentpage=2 e newpage=1
                url = f'https://www.in.gov.br/consulta/-/buscar/dou?q={keys}&s=todos&exactDate=dia&sortType=0&delta=20&currentPage={n_pages+1}&newPage={n_pages}&score=0&id=642643293&displayDate=1752721200000'
            elif n_pages > 1:
                url = f'https://www.in.gov.br/consulta/-/buscar/dou?q={keys}&s=todos&exactDate=dia&sortType=0&delta=20&currentPage={n_pages-1}&newPage={n_pages}&score=0&id=642643293&displayDate=1752721200000'
            else:
                url = f'https://www.in.gov.br/consulta/-/buscar/dou?q={keys}&s=todos&exactDate=dia&sortType=0&delta=20&currentPage={n_pages+1}&newPage={n_pages}&score=0&id=642643293&displayDate=1752721200000'
            # Fazer requisição HTTP
            self.driver.get(url)

            # Aguarda os resultados carregarem
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "col-sm-12"))
            )
            html = self.driver.page_source
            
            dfresult = self._makeScrapingOnePage(html)      
            dfresult = self._removeByKeywords(dfresult,vals_list) #removendo linhas que contenham keywords2rmn
            dfresult['Keyword'] = [keys for i in range(dfresult.shape[0])]
            

            dfinal = pd.concat([dfinal,dfresult],axis=0,ignore_index=True)

        dfinal.reset_index(drop=True,inplace=True)
        self.driver.quit()
        return dfinal
        
    
    def _makeScrapingOnePage(self,html):
        # Parser HTML com BeautifulSoup
        soup = BeautifulSoup(html, 'html.parser')
        allnews = soup.find('div', attrs={"id":"_br_com_seatecnologia_in_buscadou_BuscaDouPortlet_hierarchy_content"}).find_all('div',class_="resultados-wrapper") #pego os blocos das noticias uma a uma
        
        infosall = []
        linksall = []
        titleall = []
        txts = []
        dates = []
        for news in allnews:
            base = news.find('div',class_="resultado")

            infos = base.select("ol.dou-hierarquia.breadcrumb li")
            infos = " | ".join(item.get_text(strip=True) for item in infos)

            base_title_link = base.select_one("h5.title-marker a")
            link = "https://www.in.gov.br" + base_title_link["href"]
            title = base_title_link.get_text(strip=True)
            texto_limpo = base.select_one("p.abstract-marker").get_text(separator=" ", strip=True)

            date = base.select_one("p.date-marker").get_text(strip=True)

            infosall.append(infos)
            linksall.append(link)
            titleall.append(title)
            txts.append(texto_limpo)
            dates.append(date)
        
        data = {'Info':infosall,
                'Title':titleall,
                'Links':linksall,
                'Texts':txts,
                'Date':dates}
        
        return pd.DataFrame(data)

    def _removeByKeywords(self,df:pd.DataFrame,keywords2rmv:list|None):
        if keywords2rmv == None:
            return df
        df_ = df.copy()
        regex = "|".join(keywords2rmv)
        # Filtra com str.contains (case-insensitive)
        filtro = df_["Texts"].str.contains(regex, case=False, na=False)
        # Aplica o filtro
        df_filtrado = df_[~filtro]
        return df_filtrado.reset_index(drop=True)


    def __getChromeDriver(self):
        options = uc.ChromeOptions()
        options.headless = True  # Modo sem janela (opcional)
        driver = uc.Chrome(options=options)
        return driver

if __name__ == "__main__":
    keywords = {"medicamento":["contendo","não sujeitos","ltda"]}
    keywords = {"medicamento":None}
    keywords = {"medicamento":["contendo","não sujeitos","ltda"],
                "farmacia":["drogarias","AFE"],
                "farmacêutico":["Serviços","AFE"],
                "alimento":["locadora"]}
    sdou = ScrapingDOU()
    res = sdou.run(keywords, n_pages=1)
    print(res,res.columns)