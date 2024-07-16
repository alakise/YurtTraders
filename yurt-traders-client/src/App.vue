<template>
  <div id="app">

    <MainView/>
  </div>
</template>

<script>
import MainView from './components/MainView.vue'

export default {
  name: 'App',
  metaInfo: {
    // if no subcomponents specify a metaInfo.title, this title will be used
    title: 'YurtTraders',
    // all titles will be injected into this template
    titleTemplate: '%s | YurtTraders'
  },
  components: {
    MainView
  }
}
</script>

<style>
@import "https://cdn.jsdelivr.net/npm/@mdi/font@5.8.55/css/materialdesignicons.min.css";



.b-tabs .tabs li a:focus {
  outline: none;
  border-bottom-color: white;
}


</style>
