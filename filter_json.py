import json
from copy import deepcopy
keys_level1 = {'uuaa','name'}
keys_level2 = {'stackName','namespace','version','engine','description'}
header = list()
def filtrar_ether(json_path,output_file):
    global header
    # Se abre archivo para procesar
    f = open(json_path)
    # Carga archivo json como lista
    data = json.load(f)
    # Se filtran registros de geografía global y Colombia
    extention = obtener_salida(output_file)
    temp_list = [x for x in data if (x['geography'] == 'gl' or x['geography'] == 'co')]
    f.close()
    output_list = list()
    output_string = ''
    if extention == 'csv':
        header = list(sorted(keys_level2.union(keys_level1),reverse=True))
        output_string =';'.join(str(e) for e in header)+'\n'
    [output_list,output_string] = procesa_registros(temp_list,extention,output_list,output_string)
    with open(output_file, 'w') as outfile:
      if extention == 'csv': outfile.write(output_string)
      else: outfile.write(str(json.dumps(output_list,indent=2)))
    #return 
def obtener_salida(output_file):
    ext_pos = output_file.rfind('.')
    file_ext = output_file[-(len(output_file)-ext_pos):].lower()
    if file_ext == '.json': extention = 'json'
    else: extention = 'csv'
    return extention

def procesa_registros(temp_list,extention,output_list,output_string):
    for base_dict in temp_list:
        temp_dict = deepcopy(base_dict)
        temp_sub = deepcopy(temp_dict['majorVersions'][0])
        for h in temp_dict['majorVersions'][0].keys():
            if h not in keys_level2: temp_sub.pop(h)
        for key in base_dict.keys():
            if key not in keys_level1: temp_dict.pop(key)
        temp_dict.update(temp_sub)
        [output_list,output_string]=procesar_registro_ind(extention,output_string,temp_dict,output_list)
    return [output_list,output_string]
def procesar_registro_ind(extention,temp_string,temp_dict,temp_list):
    if extention == 'csv': 
        for data in header:
            temp_string += str(temp_dict[data] or '0')+';'
        temp_string = temp_string[:-1] + '\n'        
    else :
        temp_list.append(temp_dict)
    return [temp_list,temp_string]
if __name__=="__main__":
    filtrar_ether('data_ether.json','data_filtered.csv')