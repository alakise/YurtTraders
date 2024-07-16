<template>
  <section>
    <section class="card mb-5">
      <div class="card-header">
        <p class="card-header-title">
          Presale Information
        </p>
      </div>

      <div class="card-content">
        <div class="content">
          <b-field label="Token Address">
            <b-input v-model="contract_address" required
                     validation-message="Please provide a valid 42 character long hexadecimal (0x...) value"
                     pattern="0x[a-fA-F0-9]{40}" expanded></b-input>
          </b-field>
          <b-message
              :title="this.result"
              :closable="false"
              v-if="this.result"
              type="is-info"
              has-icon
          >
            <strong>{{ this.presaleInfo.contract_name }} ${{ this.presaleInfo.symbol }} - </strong><a target="_blank"
                                                                                                      :href="this.blockchain.scanner + 'address/' + this.presaleInfo.token">{{
              this.blockchain.scanner_name
            }}</a><br>
            <strong>Start Date:</strong> {{ this.presaleInfo.startTime | prettyTime }}<br>
            <strong>Time remaining:</strong> <span v-html="this.counterText"></span><br>
            <strong>Hard Cap:</strong> {{ this.presaleInfo.hardCap }} {{ this.blockchain.symbol }}
            <strong>Soft Cap:</strong> {{ this.presaleInfo.softCap }} {{ this.blockchain.symbol }}<br>
            <strong>Max Contribution:</strong> {{ this.presaleInfo.maxContribution }} {{ this.blockchain.symbol }}
            <strong>Min Contribution:</strong> {{ this.presaleInfo.minContribution }} {{ this.blockchain.symbol }}<br>


          </b-message>
          <b-message
              title="Invalid Address"
              :closable="false"
              v-else-if="this.error"
              type="is-danger"
              has-icon
          >
            {{ this.error }}

          </b-message>
          <b-loading :is-full-page="false" :active="this.loading" :can-cancel="true"></b-loading>
        </div>
      </div>
    </section>
    <section class="card mb-5">
      <div class="card-header">
        <p class="card-header-title">
          Make Transfer
        </p>
      </div>

      <div class="card-content">
        <div class="content">
          <div class="columns">
            <div class="column">
              <b-field label="Gas Fee">
                <b-input expanded v-model="gas">
                </b-input>
              </b-field>
            </div>
            <div class="column">
              <b-field label="Allocation">
                <b-input expanded v-model="amount">
                </b-input>
                <p class="control is-dark">
                  <span class="button is-static">{{ blockchain.symbol }}</span>
                </p>
              </b-field>
            </div>
          </div>

          <div class="buttons">
            <b-button v-on:click="transfer()" type="is-link is-outlined" expanded>Transfer Funds to Presale Address
            </b-button>
          </div>
        </div>
      </div>
    </section>
  </section>
</template>

<script>
import presale_abi from "../assets/presale_abi";
import token_abi from "../assets/token_abi"

export default {
  name: 'Presale',
  props: {
    'socket': {},
    'wallets': {},
    'blockchain': {
      default() {
        return {
          price: null, symbol: '', network: '', scanner: '', scanner_name: ''
        }
      }
    },
    'web3': {}
  },
  watch: {
    contract_address() {

      this.result = false;
      this.error = false;
      if (this.counterInterval) {
        clearInterval((this.counterInterval))
      }
      if (/^0x[a-fA-F0-9]{40}$/.test(this.contract_address)) {
        this.loading = true;
        this.getInfo().then(function () {

        }.bind(this));


      } else {
        this.contract_name = false
      }
    }
  },
  data: function () {
    return {
      contract_address: '',
      presaleAbi: presale_abi,
      tokenAbi: token_abi,
      presale: null,
      presaleInfo: {},
      result: false,
      error: false,
      counterInterval: false,
      counterText: '',
      contract: null,
      loading: false,
      gas: '7',
      amount: '1'

    }
  },
  filters: {
    abbreviateNumber(value) {
      var suffixes = ["", "K", "M", "B", "T"];
      var suffixNum = Math.floor(("" + value).length / 3);
      var shortValue = parseFloat((suffixNum !== 0 ? (value / Math.pow(1000, suffixNum)) : value).toPrecision(3));
      if (shortValue % 1 !== 0) {
        shortValue = shortValue.toFixed(2);
      }
      return shortValue + suffixes[suffixNum];
    },
    toUSD(value) {
      return value.toString().match(/[0-9]*\.0*[1-9]{0,1}[0-9]{0,3}/)[0]
    },
    prettyTime(value) {
      return value.toLocaleDateString(navigator.language) + ' ' + value.toLocaleTimeString(navigator.language)
    }
  },
  methods: {
    transfer() {
        console.log(new Date())
        this.socket.emit('transfer', {'gas': this.gas, 'amount': this.amount, 'receiver': this.contract_address})
    },
    countdown() {
      if (this.counterInterval) {
        clearInterval((this.counterInterval))
      }
      const countDownDate = this.presaleInfo.startTime;

      this.counterInterval = setInterval(function () {

        // Get todays date and time
        const now = new Date();

        // Find the distance between now and the count down date
        const distance = countDownDate - now;

        // Time calculations for days, hours, minutes and seconds
        const days = Math.floor(distance / (1000 * 60 * 60 * 24));
        const hours = Math.floor((distance % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
        const minutes = Math.floor((distance % (1000 * 60 * 60)) / (1000 * 60));
        const seconds = Math.floor((distance % (1000 * 60)) / 1000);

        // Display the result in the element with id="demo"

        if (days > 0)
          this.counterText = days + " day(s) " + hours + " hour(s) " + minutes + " minutes " + seconds + " seconds";
        else if (hours > 0)
          this.counterText = hours + " hour(s) " + minutes + " minutes " + seconds + " seconds";
        else
          this.counterText = minutes + " minutes " + seconds + " seconds";
        if (distance < 4) {
          clearInterval(this.counterInterval);
          this.counterText = "EXPIRED";
        }
      }.bind(this), 1000);
    },

    color() {
      if (this.result) {
        return 'is-info'
      } else
        return 'is-warning'
    },


    async getInfo() {

      try {
        this.presale = new this.web3.eth.Contract(this.presaleAbi, this.contract_address);
        this.presaleInfo.startTime = new Date(await this.presale.methods.startTime().call() * 1000)
        this.presaleInfo.maxContribution = await this.presale.methods.maxContribution().call() / 10 ** 18
        this.presaleInfo.minContribution = await this.presale.methods.minContribution().call() / 10 ** 18
        this.presaleInfo.hardCap = await this.presale.methods.hardCap().call() / 10 ** 18
        this.presaleInfo.softCap = await this.presale.methods.softCap().call() / 10 ** 18

        //Token info
        this.presaleInfo.token = await this.presale.methods.token().call()
        this.contract = new this.web3.eth.Contract(this.tokenAbi, this.presaleInfo.token);
        this.presaleInfo.symbol = await this.contract.methods.symbol().call();
        this.presaleInfo.contract_name = await this.contract.methods.name().call();
        this.result = "Verified PinkSale Launchpad"
        this.countdown()
        console.log(this.presaleInfo)
      } catch (e) {
        try {
          this.presale = new this.web3.eth.Contract(this.presaleAbi, this.contract_address);
          this.presaleInfo.startTime = new Date(await this.presale.methods.presaleStartTime().call() * 1000)
          this.presaleInfo.maxContribution = await this.presale.methods.maxEthContribution().call() / 10 ** 18
          this.presaleInfo.minContribution = await this.presale.methods.minEthContribution().call() / 10 ** 18
          this.presaleInfo.hardCap = await this.presale.methods.CheckHardCap().call()
          this.presaleInfo.softCap = await this.presale.methods.CheckSoftCap().call()

          //Token info
          this.presaleInfo.token = await this.presale.methods.token().call()
          this.contract = new this.web3.eth.Contract(this.tokenAbi, this.presaleInfo.token);
          this.presaleInfo.symbol = await this.contract.methods.symbol().call();
          this.presaleInfo.contract_name = await this.contract.methods.name().call();
          this.result = "Verified DxSale Launchpad"
          this.countdown()
          console.log(this.presaleInfo)
        } catch (e) {
          this.error = "Provided address is not a DxSale/PinkSale address"
          //0xa5562AAc33dB69aE571007c7E832286d83b530B1
        }
      }
      this.loading = false;


    }

  }
  ,
}
</script>

<!-- Add "scoped" attribute to limit CSS to this component only -->
<style scoped>
.button.is-static {
  background-color: rgb(41, 47, 47);
}
</style>
