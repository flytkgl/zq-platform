import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { WikiSpace } from '#/types/zq-smart-table/table'
import {
  getWikiSpacesApi,
  createWikiSpaceApi,
  updateWikiSpaceApi,
  deleteWikiSpaceApi,
  type WikiSpaceItem,
} from '#/api/smart-table'

function wikiSpaceFromApi(s: WikiSpaceItem): WikiSpace {
  return {
    id: s.id,
    name: s.name,
    icon: s.icon || 'BookOpen',
    avatar: s.avatar || null,
    description: s.description,
    cover: s.cover || null,
    category: s.category || 'default',
    visibility: s.visibility || 'private',
    documentCount: s.document_count ?? 0,
    createdAt: s.sys_create_datetime,
    updatedAt: s.sys_update_datetime,
    creatorId: s.sys_creator_id,
    creatorName: s.creator_name,
  }
}

export const useWikiStore = defineStore('wiki', () => {
  const spaces = ref<WikiSpace[]>([])
  const loading = ref(false)

  async function loadSpaces() {
    loading.value = true
    try {
      const raw = await getWikiSpacesApi()
      const list = Array.isArray(raw) ? raw : (raw as any)?.data ?? []
      spaces.value = list.map(wikiSpaceFromApi)
    } catch (e) {
      console.error('[Wiki] Failed to load spaces', e)
    } finally {
      loading.value = false
    }
  }

  async function createSpace(data: {
    name: string
    icon?: string
    avatar?: string
    description?: string
    category?: string
    visibility?: string
  }) {
    try {
      const raw = await createWikiSpaceApi(data)
      const item = (raw as any)?.data ?? raw
      const space = wikiSpaceFromApi(item)
      spaces.value.push(space)
      return space.id
    } catch (e) {
      console.error('[Wiki] Failed to create space', e)
    }
  }

  async function updateSpace(spaceId: string, data: Record<string, any>) {
    try {
      const raw = await updateWikiSpaceApi(spaceId, data)
      const item = (raw as any)?.data ?? raw
      const idx = spaces.value.findIndex((s) => s.id === spaceId)
      if (idx !== -1) {
        spaces.value[idx] = wikiSpaceFromApi(item)
      }
    } catch (e) {
      console.error('[Wiki] Failed to update space', e)
    }
  }

  async function deleteSpace(spaceId: string) {
    try {
      await deleteWikiSpaceApi(spaceId)
      spaces.value = spaces.value.filter((s) => s.id !== spaceId)
    } catch (e) {
      console.error('[Wiki] Failed to delete space', e)
    }
  }

  function $reset() {
    spaces.value = []
    loading.value = false
  }

  return {
    spaces,
    loading,
    loadSpaces,
    createSpace,
    updateSpace,
    deleteSpace,
    $reset,
  }
})
