<template>
  <section>
            <b-tabs>
              <b-tab-item label="Server Output">
                <b-button v-on:click="outputs = []" class="mb-5" type="is-secondary is-outlined" expanded>
                  Clear All Outputs
                </b-button>

                <b-message
                    v-for="output in outputs.slice().reverse()" :key="output.id"
                    :title="output.title"
                    :type="output.type ? 'is-' + output.type : null"
                >
                  <span v-html="output.message"></span>
                  <span v-if="output.decision"><hr>
                    <span v-html="output.decision.info"></span>
                    <span v-if="output.decision.contract">Contract
                      <a target="_blank" :href="blockchain.scanner + 'address/' + output.decision.contract">
                      ({{ blockchain.scanner_name }})
                      </a>
                    </span>
                  </span>
                  <b-collapse
                      v-if="output.message_content"
                      :open="false"
                  >
                    <template #trigger="props">
                      <a>
                        <b-icon :icon="!props.open ? 'menu-down' : 'menu-up'"></b-icon>
                        {{ !props.open ? 'Show message content' : 'Hide message content' }}
                      </a>
                    </template>
                    <p>
                      {{ output.message_content }}</p>
                  </b-collapse>
                </b-message>
              </b-tab-item>
            </b-tabs>
          </section>
</template>

<script>


export default {
  name: 'Log',
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
    walletByAddress(object, value) {
      if (Object.keys(object).find(key => object[key].address === value) !== undefined)
        return (parseInt(Object.keys(object).find(key => object[key].address === value)) + 1);
      else return "External"
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
