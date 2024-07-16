<template>
  <section class="card mb-5">
    <div class="card-header">
      <p class="card-header-title">
        Transfers
      </p>
    </div>

    <div class="card-content">
      <div class="content">
        <b-field label="Transfer option">
          <b-select v-on:input="receiverChange()" placeholder="Select receiver wallet(s)" v-model="receiver" expanded>
            <option
                v-for="(wallet,index) in wallets" :key="index" :value="index">
              {{
                index ? 'From main wallet to wallet ' + (index + 1) : 'Collect from all wallets to main wallet'
              }}:&nbsp;{{ wallet.address.substring(0, 8) + '......' + wallet.address.substring(36, 42) }}
            </option>
            <option
                :key="wallets.length" value="all">
              Distribute to all wallets
            </option>
          </b-select>
        </b-field>
        <b-field label="Amount">
          <b-input v-model="transfer_amount" expanded></b-input>
          <p class="control is-dark">
            <span class="button is-static">{{ blockchain.symbol }}</span>
          </p>
        </b-field>
        <div class="buttons">
          <b-button v-on:click="buttonAction()" type="is-link is-outlined" expanded>Make Transfer</b-button>
        </div>
        <p class="has-text-centered">
          <span v-if="receiver==='all' && wallets.length > 0">
            Your main wallet will send {{ transfer_amount }}&nbsp;{{ blockchain.symbol }}&nbsp;
            each to all other wallets you have.<br>
            <span v-if="wallets[0].balance - (wallets.length - 1) * transfer_amount > 0">
            There will be {{ parseFloat(wallets[0].balance - (wallets.length - 1) * transfer_amount).toFixed(5) }}&nbsp;{{
                blockchain.symbol
              }} in your main wallet,<br>excluding gas fee expenses.
              </span>
            <span v-else class="has-text-danger">
              Balance is not enough for transaction.
            </span>
          </span>
          <span v-else-if="wallets.length > 0 && receiver === 0">
            All balance will be sent to main wallet.
          </span>
          <span v-else>
            Your main wallet will send {{ transfer_amount }}&nbsp;{{ blockchain.symbol }}&nbsp;
            to the selected wallet.<br>
            <span v-if="wallets.length > 0 && wallets[0].balance - transfer_amount > 0">
            There will be {{ parseFloat(wallets[0].balance - transfer_amount).toFixed(5) }}&nbsp;{{
                blockchain.symbol
              }} in your main wallet,<br>excluding gas fee expenses.
              </span>
            <span v-else class="has-text-danger">
              Balance is not enough for transaction.
            </span>
          </span>
        </p>
      </div>
    </div>
  </section>
</template>

<script>


export default {
  name: 'Transfers',
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
      receiver: 'all',
      transfer_amount: 0.12
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
    },
    receiverChange() {
      console.log(this.receiver)
    },
    buttonAction(){
      if(this.receiver === 'all'){
        this.distribute()
      }else if(this.receiver === 0){
        this.collect()
      }
    },
    distribute(){
      if(this.wallets[0].balance - (this.wallets.length - 1) * this.transfer_amount > 0)
      {
        this.send('distribute', {'amount': this.transfer_amount})
      }else{
        this.$buefy.toast.open('There is not enough balance in the wallet for that transfer')
      }
    },
    collect(){
      this.send('collect', {})
    }
  },
}
</script>

<!-- Add "scoped" attribute to limit CSS to this component only -->
<style scoped>
.button.is-static {
  background-color: rgb(41, 47, 47);
}
</style>
