import Vue from 'vue'
import App from './App.vue'
import Buefy from "buefy";
import 'buefy/dist/buefy.css'
let a = true;
if (a) {
    import('buefy/dist/dark.min.css');
}


import Store from "./components/Store";
import InputTag from "vue-input-tag";

Vue.config.productionTip = false
Vue.use(Buefy)
Vue.component('input-tag', InputTag)
import VueMeta from 'vue-meta'

Vue.use(VueMeta)
new Vue({
    render: h => h(App),
    Store
}).$mount('#app')
