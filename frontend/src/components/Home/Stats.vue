<script setup lang="ts">
import api from "@/services/api/index";
import { formatBytes } from "@/utils";
import { onBeforeMount, ref } from "vue";
import { useI18n } from "vue-i18n";

const { t } = useI18n();
const stats = ref({
  PLATFORMS: 0,
  ROMS: 0,
  SAVES: 0,
  STATES: 0,
  SCREENSHOTS: 0,
  TOTAL_FILESIZE_BYTES: 0,
});

onBeforeMount(() => {
  api.get("/stats").then(({ data }) => {
    stats.value = data;
  });
});
</script>
<template>
  <v-card class="ma-2">
    <v-card-text class="pa-1">
      <v-row no-gutters class="flex-nowrap overflow-x-auto text-center">
        <v-col>
          <v-chip
            class="text-overline"
            prepend-icon="mdiController"
            variant="text"
            label
          >
            {{ t("common.platforms-n", stats.PLATFORMS) }}
          </v-chip>
        </v-col>
        <v-col>
          <v-chip
            class="text-overline"
            prepend-icon="mdiDisc"
            variant="text"
            label
          >
            {{ t("common.games-n", stats.ROMS) }}
          </v-chip>
        </v-col>
        <v-col>
          <v-chip
            class="text-overline"
            prepend-icon="mdiContentSave"
            variant="text"
            label
          >
            {{ t("common.saves-n", stats.SAVES) }}
          </v-chip>
        </v-col>
        <v-col>
          <v-chip
            class="text-overline"
            prepend-icon="mdiFile"
            variant="text"
            label
          >
            {{ t("common.states-n", stats.STATES) }}
          </v-chip>
        </v-col>
        <v-col>
          <v-chip
            class="text-overline"
            prepend-icon="mdiImageArea"
            variant="text"
            label
          >
            {{ t("common.screenshots-n", stats.SCREENSHOTS) }}
          </v-chip>
        </v-col>
        <v-col>
          <v-chip
            class="text-overline"
            prepend-icon="mdiHarddisk"
            variant="text"
            label
          >
            {{ t("common.size-on-disk") }}:
            {{ formatBytes(stats.TOTAL_FILESIZE_BYTES, 1) }}
          </v-chip>
        </v-col>
      </v-row>
    </v-card-text>
  </v-card>
</template>
