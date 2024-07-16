<template>
  <section class="card mb-5">
    <div class="card-header">
      <p class="card-header-title">
        Wallets
      </p>
    </div>

    <div class="card-content">
      <div class="content">
        <nav class="panel">
          <div class="panel-block">
            <p class="control has-icons-left">
              <input class="input" v-model="walletSearch" type="text" placeholder="Search">
              <span class="icon is-left">
        <i class="mdi mdi-magnify mdi-18px" aria-hidden="true"></i>
      </span>
            </p>
          </div>
          <a v-for="(wallet,index) in filteredWallets" :key="index"
             :class="{'panel-block':true, 'has-text-info': index === 0}">
    <span class="panel-icon">
      <i class="mdi mdi-credit-card mdi-18px" aria-hidden="true"></i>
    </span>
            <b-tooltip type="is-light" label="Show full address">
                            <span
                                v-on:click="alert('Wallet ' + (index + 1) + ' - Nonce: ' + wallet.nonce, `<span class='tag is-light is-medium'>${wallet.address}</span>`)">
                              {{ wallet.address.substring(0, 8) + '......' + wallet.address.substring(36, 42) }}
                            </span>
            </b-tooltip>
            &nbsp;&nbsp;&nbsp;
            <span v-if="wallet.balance > 0">{{ parseFloat(wallet.balance).toFixed(4) }} {{ blockchain.symbol }}</span>
            <span v-else>(  empty  )</span>

            <b-tooltip type="is-light" :label="'Open wallet in ' + blockchain.scanner_name">
              <a class="ml-5" :href="`${blockchain.scanner}address/${wallet.address}`" target="_blank"><i
                  class="mdi mdi-open-in-new mdi-24px"></i></a>
            </b-tooltip>
            <span class="ml-5" v-if="index === 0"> (main wallet)</span>
          </a>

          <div class="panel-block">

            <button v-on:click="send('refresh_wallet', {login: false})"
                    class="button is-link is-outlined is-fullwidth">
              <i class="mdi mdi-refresh mdi-24px" aria-hidden="true"></i> Refresh Wallets
            </button>
          </div>
        </nav>
        <a>
          Total Balance: {{ totalBalance }} {{ blockchain.symbol }}
        </a>
      </div>
    </div>
  </section>
</template>

<script>


export default {
  name: 'Wallets',
  props: {
    'socket': {},
    'wallets': {},
    'blockchain': {
      default() {
        return {
          price: null, symbol: '', network: '', scanner: '', scanner_name: ''
        }
      }
    }
  },
  data: function () {
    return {
      walletSearch: ''
    }
  },
  computed: {
    filteredWallets() {
      if (this.wallets.length > 0) {
        return this.wallets.filter(item => {
          return item.address.toLowerCase().indexOf(this.walletSearch.toLowerCase()) > -1
        })
      } else {
        return {}
      }
    },
    totalBalance() {
      let total = 0
      this.wallets.forEach(function (item) {
        total += parseFloat(item.balance);
      })
      return total;
    }
  },
  methods: {
    send(event, args) {
      this.socket.emit(event, args);
    },
    alert(title, message) {
      this.$buefy.dialog.alert({
        title: title,
        message: message,
      })
    }
  }
}
</script>

<!-- Add "scoped" attribute to limit CSS to this component only -->
<style scoped>
.panel-block:not(:last-child), .panel-tabs:not(:last-child) {
  border-bottom: 1px solid darkslategrey;
}
</style>
