#PACKAGES

import folium
import streamlit as st
from streamlit_folium import folium_static
import pandas as pd
import geopandas as gpd
from shapely import wkt


st.set_page_config(layout="wide")

#-----------------------------------------------------------------------------------------------------
##FUNCTIONS
#activity filter
def activity_filter(activity_desc, cnaes, df_state_atictivities_size, all_msg):

    #dataframe filtered if all activities are chosen 
    if activity_desc==all_msg:
        cnae_code = cnaes.loc[:, 'cnae_code'].tolist()
        df_filtered = df_state_atictivities_size.copy()
        cnae_message = '**Atividade:** Todas atividades exercidas pelos clientes Hexagon'
    #dataframe filtered if just one activity is chosen
    else:
        cnae_code = cnaes.loc[cnaes['desc_activity']==activity_desc, 'cnae_code'].tolist()
        df_filtered = df_state_atictivities_size[df_state_atictivities_size[str(cnae_code[0])]==1]
        cnae_message = "**Atividade:** " +activity_desc.capitalize() 
     
    return(df_filtered, cnae_code, cnae_message)
  
#state filter  
def state_filter(df_filtered, state_option, all_msg):
    #dataframe filtered if all states are chosen 
    if state_option==all_msg:
        zoom=4 #zoom_start
        state_message='**Estado:** Todos estados'
    #dataframe filtered if just one state is chosen
    else:
        df_filtered = df_filtered[df_filtered['uf']==state_option].copy()
        zoom=5.5 #zoom start for geo map
        state_message= '**Estado: **' +state_option
    return(df_filtered, state_message, zoom)

#quantity and percentage companies in the cards
def percentage_df(column, df_cards):
    absolute_number = df_cards[column]
    percentage=str(int(100*(df_cards[column]/df_cards['All sizes'])))
    return absolute_number, percentage
    
 
#dataframe filtered ploted in the map
def map_plot(df_filtered, count_map):

    x=count_map['geometry'].centroid.x.mean()
    y=count_map['geometry'].centroid.y.mean()

    m = folium.Map(location=[y, x], zoom_start = zoom, tiles=None,overlay=False) #tiles=None)#'CartoDB positron',overlay=True)#tiles='CartoDB positron')

    for column_name in ['Sem Parceria', 'Parceiros']:
        

        myscale = (count_map[column_name].quantile((0,0.1,0.75,0.9,0.98,1))).tolist()
        feature_group = folium.FeatureGroup(name=column_name,overlay=False).add_to(m)

        # Set up Choropleth map
        choropleth1 = folium.Choropleth(
        geo_data=count_map,
        data=count_map,
        columns=['uf',column_name],
        key_on="feature.properties.uf",
        fill_color='YlGnBu',
        fill_opacity=1,
        line_opacity=0.2,
        threshold_scale=myscale,
        legend_name="Number of Companies ("+column_name+')',
        smooth_factor=0,
        Highlight= True,
        line_color = "#0000",
        name = column_name,
        show=True,
        #overlay=False,
        nan_fill_color = "White"
        ).geojson.add_to(feature_group)#add_to(m)

        style_function = lambda x: {'fillColor': '#ffffff',
                                    'color':'#000000',
                                    'fillOpacity': 0.1,
                                    'weight': 0.1}
        highlight_function = lambda x: {'fillColor': '#000000',
                                        'color':'#000000',
                                        'fillOpacity': 0.50,
                                        'weight': 0.1}
        NIL = folium.features.GeoJson(
            count_map,
            style_function=style_function,
            control=False,
            highlight_function=highlight_function,
            tooltip=folium.features.GeoJsonTooltip(
                fields=['uf',column_name],
                aliases=['State: ','Number of Companies: '],
                style=("background-color: white; color: #333333; font-family: arial; font-size: 12px; padding: 10px;")
            )
        ).add_to(choropleth1)

    folium.TileLayer('cartodbpositron',overlay=True,name="Map").add_to(m)
    folium.LayerControl(collapsed=False).add_to(m)

    folium_static(m)


#----------------------------------------------------------------------------------------------------- 
#DATAFRAMES
#states geo dataset
gdf=pd.read_csv(r'./files/estados_n_empresas.csv')
#st.dataframe(gdf.head())

#active companies quantity in Brazil grouped by uf, city, size and acoustic activity 
df_state_atictivities_size= pd.read_csv(r'./files/empresas_atividades_mapa_parceria.csv')
#st.dataframe(df_state_atictivities_size.head())


#activity code dataset (acoustics cnaes)
cnaes = pd.read_csv(r'./files/activities_code.csv')
activities = cnaes['desc_activity'].tolist()

clientes_hexagon = pd.read_excel(r'./files/clientes HEXAGON.xlsx').dropna(how='all')

empresas_hexagon = pd.read_csv(r'./files/empresas_descritivos_parceiros.csv')

#st.text(clientes_hexagon['Estado'].unique().tolist())
#-----------------------------------------------------------------------------------------------------
#PAGE STRUCTURE
st.title('Empresas do Agronegócio')

st.sidebar.subheader('Atividades exercidas pelos clientes Hexagon')

#FILTERS
#activity filter sidebar
all_msg = 'Todos'
activity_desc = st.sidebar.selectbox('Escolha a atividade',[all_msg] + activities)

lista_state= [all_msg] + gdf['uf'].unique().tolist()
state_option = st.sidebar.selectbox('Escolha o Estado',lista_state)




    
if state_option != all_msg:
    clientes_hexagon = clientes_hexagon[clientes_hexagon['Estado']==state_option].copy()
    empresas_hexagon = empresas_hexagon[empresas_hexagon['uf']==state_option].copy()


if state_option == 'EX':
    pass
else:

    #filtering by activity
    df_filtered, cnae_code, cnae_message = activity_filter(activity_desc, cnaes, df_state_atictivities_size, all_msg)
    #st.text(cnae_code)
    #st.dataframe(df_filtered)

    #filtering by state   
    df_filtered, state_message, zoom = state_filter(df_filtered, state_option, all_msg)
        
    #dataframe grouped by state and activity chosen in the filter
    df_filtered = df_filtered.groupby(['uf','porte']).sum()[['cnpj_basico']].reset_index()
    #dataframe organized by state and size
    df_filtered = pd.pivot_table(df_filtered, values='cnpj_basico', index='uf', columns='porte')
    #df_filtered = df_filtered.rename(columns=dict_porte)
    #column with sum of sizes
    df_filtered['All sizes']= df_filtered.sum(axis=1)
    #st.dataframe(df_filtered)

    #dataframe filtered and organized merging with geolocation (dataframe gdf)
    df_filtered = df_filtered.merge(gdf, left_on='uf', right_on = 'UF_05')
    #st.dataframe(df_filtered)

    #card numbers with companies quantity
    df_cards = df_filtered[df_filtered.columns[:4]].sum().astype(int)
    #st.dataframe(df_cards)#.astype(int))

    #Chosen activity and state
    st.write(cnae_message)
    st.write(state_message)

    #Quantity and percentage companies in the cards
    col1, col2, col3 = st.columns(3)
    col1.metric("Todas empresas", str(df_cards['All sizes']))

    column_names = ['Sem Parceria', 'Parceiros']
    columns = [col2, col3]
    for col, col_name in zip(columns, column_names):
        absolute_number, percentage = percentage_df(col_name, df_cards)
        col.metric(col_name, str(absolute_number), percentage+'%')

    #st.dataframe(gdf)
    df_filtered['geometry'] = df_filtered['geometry'].apply(wkt.loads)
    count_map = gpd.GeoDataFrame(df_filtered, geometry='geometry', crs='epsg:4326')

    #plotting dataframe filteres
    map_plot(df_filtered, count_map)

    url = 'https://www.gov.br/receitafederal/pt-br/assuntos/orientacao-tributaria/cadastros/consultas/dados-publicos-cnpj'
    st.markdown("[Data](url) from 15/10/2021")

len_empresas_hexagon = len(empresas_hexagon)
len_clientes_hexagon = len(clientes_hexagon)

import plotly.graph_objects as go

labels = ['Empresas - CNPJ','CPF']
values = [len_empresas_hexagon, len_clientes_hexagon - len_empresas_hexagon]

fig = go.Figure(data=[go.Pie(labels=labels, values=values)])

fig.update_layout(
    title="Composição clientes Hexagon - Estado: "+state_option)


st.plotly_chart(fig)

st.write('Número de clientes carteira Hexagon - CNPJ:', str(len_empresas_hexagon))
st.dataframe(empresas_hexagon[['nome_fantasia', 'uf', 'cnpj_basico', 'porte']])

st.write('Número de clientes carteira Hexagon:', str(len_clientes_hexagon))
st.dataframe(clientes_hexagon)