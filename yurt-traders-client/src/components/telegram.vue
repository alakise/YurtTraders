<template>
  <section class="card mb-5">
    <div class="card-header">
      <p class="card-header-title">
        Telegrams
      </p>
    </div>

    <div class="card-content">
      <div class="content">
        <nav class="panel">
          <div class="panel-block">
            <p class="control has-icons-left">
              <input class="input" v-model="telegramSearch" type="text" placeholder="Search">
              <span class="icon is-left">
        <i class="mdi mdi-magnify mdi-18px" aria-hidden="true"></i>
      </span>
            </p>
          </div>
          <div class="mt-2 mb-2" v-for="(item,index) in filteredTelegrams" :key="index">
    <span class="panel-icon">
      <i class="mdi mdi-account-box mdi-24px" aria-hidden="true"></i>
    </span>
            {{ item.name }}  <code class="is-family-code">{{ item.id.toString().replace('-100', '-') }}</code><br>
          </div>

          <div class="panel-block">

            <button v-on:click="socket.emit('telegram_dialogues')"
                    class="button is-link is-outlined is-fullwidth">
              <i class="mdi mdi-refresh mdi-24px" aria-hidden="true"></i> Refresh Wallets
            </button>
          </div>
        </nav>

      </div>
    </div>
  </section>
</template>

<script>
export default {
  name: 'Telegram',
  props: {
    'socket': {},
    'wallets': {},
    'contract': {},

    'blockchain': {
      default() {
        return {
          price: null, symbol: '', network: '', scanner: '', scanner_name: ''
        }
      }
    },

  },
  computed: {
    filteredTelegrams() {
      if (this.telegrams.length > 0) {

        return this.telegrams.filter(item => {
          return item.name.toLowerCase().indexOf(this.telegramSearch.toLowerCase()) > -1
        })
      } else {
        return {}
      }
    }
  },
  data: function () {
    return {
      telegrams: [],
      telegramSearch: ''
    }
  },
  methods: {}
  ,
  mounted() {
    this.socket.on("dialogues", (e) => {
      console.log("Dialogue list refreshed.", e.dialogues)
      this.telegrams = e.dialogues;
    });
  }
}
</script>
<style scoped>
.panel-block:not(:last-child), .panel-tabs:not(:last-child) {
  border-bottom: 1px solid darkslategrey;
}
</style>