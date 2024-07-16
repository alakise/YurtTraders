<template>
  <section class="card mb-5">
    <div class="card-header">
      <p class="card-header-title">
        Sell
      </p>
    </div>

    <div class="card-content">
      <div class="content">
        <b-field>
          <b-select value="0" v-model="wallet_count" expanded placeholder="Sell tokens on first ... wallets">
            <option
                v-for="(wallet,index) in wallets" :key="index + 1" :value="index + 1">
              {{ 'Sell tokens on first ' + (index + 1) }} wallets

            </option>
          </b-select>
        </b-field>
        <b-button v-on:click="sell()" type="is-link is-outlined" expanded>
          Sell first {{ wallet_count }} wallets.
        </b-button>

      </div>
    </div>
  </section>
</template>

<script>
export default {
  name: 'Approve',
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
  data: function () {
    return {
      wallet_count: 1,
      gasLimit: 0,
    }
  },
  methods: {
    sell() {
      this.socket.emit('sell', {
        contract: this.contract,
        count: this.wallet_count
      })
    },
    calculateGas() {
      this.socket.emit('sell_gas', {'contract': this.contract})
    }
  },
  mounted() {
    this.socket.on("sell_gas_response", (e) => {
      console.log(e)
    });
  }
}
</script>