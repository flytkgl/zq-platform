import { requestClient } from '#/api/request';

export namespace RegionApi {
  // 省份相关接口
  export function getProvinces() {
    return requestClient.get('/api/core/regions/provinces');
  }

  export function createProvince(data: any) {
    return requestClient.post('/api/core/regions/provinces', data);
  }

  export function updateProvince(id: string, data: any) {
    return requestClient.put(`/api/core/regions/provinces/${id}`, data);
  }

  export function deleteProvince(id: string) {
    return requestClient.delete(`/api/core/regions/provinces/${id}`);
  }

  // 城市相关接口
  export function getCities(provinceCode?: string) {
    return requestClient.get('/api/core/regions/cities', {
      params: { province_code: provinceCode },
    });
  }

  export function createCity(data: any) {
    return requestClient.post('/api/core/regions/cities', data);
  }

  export function updateCity(id: string, data: any) {
    return requestClient.put(`/api/core/regions/cities/${id}`, data);
  }

  export function deleteCity(id: string) {
    return requestClient.delete(`/api/core/regions/cities/${id}`);
  }

  // 区县相关接口
  export function getAreas(cityCode?: string) {
    return requestClient.get('/api/core/regions/areas', {
      params: { city_code: cityCode },
    });
  }

  export function createArea(data: any) {
    return requestClient.post('/api/core/regions/areas', data);
  }

  export function updateArea(id: string, data: any) {
    return requestClient.put(`/api/core/regions/areas/${id}`, data);
  }

  export function deleteArea(id: string) {
    return requestClient.delete(`/api/core/regions/areas/${id}`);
  }

  // 街道相关接口
  export function getStreets(areaCode?: string) {
    return requestClient.get('/api/core/regions/streets', {
      params: { area_code: areaCode },
    });
  }

  export function createStreet(data: any) {
    return requestClient.post('/api/core/regions/streets', data);
  }

  export function updateStreet(id: string, data: any) {
    return requestClient.put(`/api/core/regions/streets/${id}`, data);
  }

  export function deleteStreet(id: string) {
    return requestClient.delete(`/api/core/regions/streets/${id}`);
  }

  // 村庄相关接口
  export function getVillages(streetCode?: string) {
    return requestClient.get('/api/core/regions/villages', {
      params: { street_code: streetCode },
    });
  }

  export function createVillage(data: any) {
    return requestClient.post('/api/core/regions/villages', data);
  }

  export function updateVillage(id: string, data: any) {
    return requestClient.put(`/api/core/regions/villages/${id}`, data);
  }

  export function deleteVillage(id: string) {
    return requestClient.delete(`/api/core/regions/villages/${id}`);
  }

  // 获取树形数据
  export function getRegionTree(level: number = 3) {
    return requestClient.get('/api/core/regions/tree', {
      params: { level },
    });
  }
}
