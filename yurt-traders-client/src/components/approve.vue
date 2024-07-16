<template>
  <section class="card mb-5">
    <div class="card-header">
      <p class="card-header-title">
        Approval
      </p>
    </div>

    <div class="card-content">
      <div class="content">
        <b-field>
          <b-select value="0" v-model="wallet" expanded placeholder="Approve for wallet...">
            <option
                v-for="(wallet,index) in wallets" :key="index"  :value="index">
              {{ 'Wallet ' + (index + 1) }} :
              {{ wallet.address.substring(0, 8) + '......' + wallet.address.substring(36, 42) }}
            </option>
          </b-select>
          <p class="control">
            <b-button v-on:click="approve(false)" type="is-link" label="Approve"/>
          </p>
        </b-field>
        <b-field>
          <b-switch v-model="checkBalance">
            {{
              checkBalance ? 'Wallets without balance won\'t get approved ' : 'Selected wallet(s) will get approved without balance check.'
            }}
          </b-switch>
        </b-field>
        <b-button v-on:click="approve(true)" type="is-link is-outlined" expanded>
          Approve All Wallets
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
      checkBalance: false,
      wallet: 0
    }
  },
  methods: {
    approve(all = false){
      this.socket.emit('approve',{
        contract: this.contract,
        check_balance: this.checkBalance,
        all:all,
        wallet:this.wallet

      })
    }
  }
  ,
}
</script>