<script setup lang="ts">
import Task from "@/components/Settings/Administration/TaskOption.vue";
import RSection from "@/components/common/RSection.vue";
import api from "@/services/api/index";
import type { TaskInfo } from "@/__generated__/models/TaskInfo";
import { convertCronExperssion } from "@/utils";
import { computed, onMounted, ref } from "vue";

const tasks = ref<{
  watcher: TaskInfo[];
  scheduled: TaskInfo[];
  manual: TaskInfo[];
}>({
  watcher: [],
  scheduled: [],
  manual: [],
});

const watcherTasks = computed(() =>
  tasks.value.watcher.map((task) => ({
    ...task,
    icon: task.enabled ? "mdiFileCheckOutline" : "mdiFileRemoveOutline",
  })),
);

const scheduledTasks = computed(() =>
  tasks.value.scheduled.map((task) => ({
    ...task,
    description:
      task.description + " " + convertCronExperssion(task.cron_string),
    icon: task.enabled ? "mdiClockCheckOutline" : "mdiClockRemoveOutline",
    cron_string: convertCronExperssion(task.cron_string),
  })),
);

// Icon mapping for manual tasks
const getManualTaskIcon = (taskName: string) => {
  const iconMap: Record<string, string> = {
    cleanup_orphaned_resources: "mdiBroom",
  };
  return iconMap[taskName] || "mdiPlay";
};

const manualTasks = computed(() =>
  tasks.value.manual.map((task) => ({
    ...task,
    icon: getManualTaskIcon(task.name),
  })),
);

const getAvailableTasks = async () => {
  await api.get("/tasks").then((response) => {
    tasks.value = response.data;
  });
};

onMounted(() => {
  getAvailableTasks();
});
</script>
<template>
  <r-section icon="mdiPulse" title="Tasks" class="ma-2">
    <template #toolbar-append> </template>
    <template #content>
      <v-chip label variant="text" prepend-icon="mdiFolderEye" class="ml-2 mt-1"
        >Watcher</v-chip
      >
      <v-divider class="border-opacity-25 ma-1" />
      <v-row no-gutters class="align-center py-1">
        <v-col cols="12" md="6" v-for="task in watcherTasks">
          <task
            class="ma-3"
            :enabled="task.enabled"
            :title="task.title"
            :description="task.description"
            :icon="task.icon"
          />
        </v-col>
      </v-row>

      <v-chip label variant="text" prepend-icon="mdiClock" class="ml-2 mt-1"
        >Scheduled</v-chip
      >
      <v-divider class="border-opacity-25 ma-1" />
      <v-row no-gutters class="align-center py-1">
        <v-col cols="12" md="6" v-for="task in scheduledTasks">
          <task
            class="ma-3"
            :enabled="task.enabled"
            :title="task.title"
            :description="task.description"
            :icon="task.icon"
            :name="task.name"
            :manual_run="task.manual_run"
            :cron_string="task.cron_string"
          />
        </v-col>
      </v-row>
      <v-row no-gutters class="align-center py-1">
        <v-chip
          label
          variant="text"
          prepend-icon="mdiGestureDoubleTap"
          class="ml-2 mt-1"
          >Manual</v-chip
        >
        <v-divider class="border-opacity-25 ma-1" />
        <v-col cols="12" md="6" v-for="task in manualTasks">
          <task
            class="ma-3"
            :title="task.title"
            :description="task.description"
            :icon="task.icon"
            :name="task.name"
            :manual_run="task.manual_run"
          />
        </v-col>
      </v-row>
    </template>
  </r-section>
</template>
