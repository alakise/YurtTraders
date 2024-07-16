<template>
  <section>
    <section class="card mb-5">
      <div class="card-header">
        <p class="card-header-title">
          Token Analyse
        </p>
      </div>

      <div class="card-content">
        <div class="content">
          <b-field label="Token Address">
            <b-input v-model="contractAddress" required
                     validation-message="Please provide a valid 42 character long hexadecimal (0x...) value"
                     pattern="0x[a-fA-F0-9]{40}" expanded></b-input>
          </b-field>
          <b-message
              title="Token Information"
              :closable="false"
              v-if="contract_name"
              :type="color()"
              has-icon
              aria-close-label="Close message">
            <strong>Token:</strong>&nbsp;{{ contract_name }} ${{ symbol }}<br>
            <span v-if="!isNaN(price) && price !== -1">
          <strong>Price:</strong> {{ parseFloat(price).toFixed(8) || toUSD }} $<br>
          <strong>LP Size:</strong> {{ parseFloat(pairSize).toFixed(2) }} {{ this.blockchain.symbol }}<br>
          <strong>Market Cap:</strong> {{ parseInt(marketCap) | abbreviateNumber }} $<br>
            </span>
            <span v-if="sell_tax !== -1">
          <strong>Buy Tax:</strong> {{ this.buy_tax }}% <strong>Sell Tax:</strong> {{ this.sell_tax }}%<br>
          <strong>Buy Gas:</strong> {{ this.buy_gas }} Wei <strong>Sell Tax:</strong> {{ this.buy_gas }} Wei
            <br>
          </span><br>
            <span v-if="contract_name && walletBalance.length > 0">
              <span v-for="(wallet,index) in walletBalance" :key="index">
                  <span v-if="wallet.price_usd > 0"><b>Wallet {{ index + 1 }}</b>: {{
                      wallet.price_usd
                    }}$ - {{ wallet.price }} {{ blockchain.symbol }}<br></span>
              </span>
              <a v-on:click="getWalletBalance()">Refresh</a>
            </span>
            <span v-if="error">
            {{ error }}
          </span>
          </b-message>
        </div>
      </div>
    </section>
    <approve v-bind:wallets="wallets" v-bind:blockchain="blockchain"
             v-bind:socket="socket" v-bind:contract="contractAddress"></approve>
    <sell v-bind:wallets="wallets" v-bind:blockchain="blockchain"
          v-bind:socket="socket" v-bind:contract="contractAddress"></sell>
    <section class="card mb-5">
      <div class="card-header">
        <p class="card-header-title">
          Sniper
        </p>
      </div>

      <div class="card-content">
        <div class="content">
          <div class="columns">
            <div class="column">
              <b-field label="Max Buy Tax (%)">
                <b-input :disabled="sniper.orderActive" v-model="sniper.maxBuyTax"></b-input>
              </b-field>
            </div>
            <div class="column">
              <b-field label="Max Sell Tax (%)">
                <b-input :disabled="sniper.orderActive" v-model="sniper.maxSellTax"></b-input>
              </b-field>
            </div>
            <div class="column">
              <b-field label="Max Total Tax (%)">
                <b-input :disabled="sniper.orderActive" v-model="sniper.maxTotalTax"></b-input>
              </b-field>
            </div>
            <div class="column">
              <b-field label="Scan Threshold (ms)">
                <b-input :disabled="sniper.orderActive" v-model="sniper.scanThreshold"></b-input>
              </b-field>
            </div>

          </div>
          <div class="columns">
            <div class="column">
              <b-field label="Buy Amount">
                <b-input :disabled="sniper.orderActive" v-model="sniper.buyAmount"></b-input>
              </b-field>
            </div>

            <div class="column">
              <b-field label="Wallets">
                <b-numberinput min="1" :disabled="sniper.orderActive" v-model="sniper.walletCount"
                               :max="this.wallets.length"></b-numberinput>
              </b-field>
            </div>
            <div class="column">
              <b-field label="Repeat">
                <b-input :disabled="sniper.orderActive" v-model="sniper.repeat"></b-input>
              </b-field>
            </div>

          </div>


          <b-button :type="sniper.orderActive ? 'is-danger is-outlined' :'is-link is-outlined'" v-on:click="buy_order()"
                    :disabled="!this.contract_name" expanded>
            {{ sniper.orderActive ? 'Disable Order' : (buy_permission() ? 'Buy Immediately ' : 'Buy When Available') }}
          </b-button>

          <p class="has-text-centered mt-1">
            <span v-if="!contract_name" class="has-text-warning">Please provide a valid contract address first</span>
            <span v-else-if="buy_permission()" class="has-text-info">All conditions are met. Clicking to button will make IMMEDIATE buy.</span>
            <span v-else class="has-text-info">If trade is enabled and conditions are met buy order will be completed. Buy order can be cancelled any time.</span>
          </p>
          <p class="has-text-centered mt-1">
            {{ this.sniper.workerInfo }}
          </p>

        </div>
      </div>
    </section>

  </section>
</template>

<script>
import tokenAbi from "../assets/token_abi"
import uniAbi from "../assets/uni_abi"
import uniFactoryAbi from "../assets/uni_factory_abi"
import pairAbi from "../assets/pair_abi"
import Approve from "./approve";
import Sell from "./sell";

export default {
  name: 'contract',
  components: {Approve, Sell},
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
    'web3': {},
    'activeContract': {}
  },
  watch: {
    contractAddress() {
      if (this.sniper.orderActive) {
        this.sniper.orderActive = false;
        clearInterval(this.sniper.interval)
      }
      if (/^0x[a-fA-F0-9]{40}$/.test(this.contractAddress)) {
        this.walletBalance = []
        this.contract = new this.web3.eth.Contract(this.tokenAbi, this.contractAddress);
        this.router = new this.web3.eth.Contract(this.uniAbi, this.blockchain.router);
        this.factory = new this.web3.eth.Contract(this.uniFactoryAbi, this.blockchain.factory)
        this.getInfo().then((info_provided) => {
          if (info_provided) {
            this.priceCalculation().then(() => {
              this.getWalletBalance()

            })
            if (this.blockchain.network === 'BSC')
              this.honeypot()

          }

        });


      } else {
        this.contract_name = false
        this.sell_tax = -1
        this.buy_tax = -1
        this.walletBalance = []
      }
    },
    activeContract() {
      this.contractAddress = this.activeContract
    },
  },
  data: function () {
    return {
      contractAddress: '',
      tokenAbi: tokenAbi,
      uniAbi: uniAbi,
      uniFactoryAbi: uniFactoryAbi,
      pairAbi: pairAbi,
      contract: null,
      router: null,
      factory: null,
      contract_name: false,
      symbol: false,
      marketCap: 0,
      price: -1,
      price_as_bnb: -1,
      pairSize: 0,
      buy_tax: -1,
      sell_tax: -1,
      buy_gas: 0,
      sell_gas: 0,
      tokenSupply: 0,
      error: false,
      walletBalance: [],
      decimals: 8,
      sniper: {
        scanThreshold: 1000,
        buyAmount: 0.1,
        maxBuyTax: 21,
        maxSellTax: 21,
        maxTotalTax: 42,
        walletCount: 1,
        orderActive: false,
        interval: null,
        workerInfo: '',
        repeat: 1

      }
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
    }
  },
  methods: {
    async getWalletBalance() {
      this.walletBalance = this.wallets
      for (let i = 0; i < this.walletBalance.length; i++) {
        this.updateBalance(this.walletBalance[i], i)

      }
      console.log(this.walletBalance)
    },
    async updateBalance(item, i) {
      const token = new this.web3.eth.Contract(this.tokenAbi, this.contractAddress)
      let balance = await token.methods.balanceOf(item.address).call()
      if (balance >= 1)
        item.price = await this.simulateSell(balance)
      item.price = item.price * 10 ** -18
      item.price_usd = (item.price * this.blockchain.price).toFixed(2)
      item.price = item.price.toFixed(5)
      this.walletBalance[i] = item;
    },
    async getInfo() {
      try {
        this.symbol = await this.contract.methods.symbol().call();
        this.contract_name = await this.contract.methods.name().call();
        return true;
      } catch (e) {
        this.$buefy.toast.open({
          duration: 5000,
          message: `Error: address provided is not a token or you are on the wrong network.`,
          position: 'is-top',
          type: 'is-danger'
        })
        this.walletBalance = []
        this.contract_name = this.symbol = false;
        return false;
      }
    },
    buy() {
      this.socket.emit('buy', {
        amount: this.sniper.buyAmount,
        wallets: this.sniper.walletCount,
        repeat: this.sniper.repeat,
        contract: this.contractAddress
      })
    },
    buy_permission() {
      if (this.blockchain.network !== 'BSC')
        return true
      return this.buy_tax !== -1 && this.sell_tax !== -1
          && this.buy_tax < this.sniper.maxBuyTax && this.sell_tax < this.sniper.maxSellTax
          && this.buy_tax + this.sell_tax < this.sniper.maxTotalTax;

    },
    buy_order() {
      if (this.sniper.orderActive) {
        this.sniper.orderActive = false;
        clearInterval(this.sniper.interval)
      } else {
        if (this.buy_permission()) {
          this.buy()
        } else {
          this.sniper.orderActive = true;
          this.sniper.interval = setInterval(this.scan.bind(this), this.sniper.scanThreshold);
        }
      }

    },
    scan() {

      let today = new Date();
      let time = ('0' + today.getHours().toString()).slice(-2) + ":" + ('0'
              + today.getMinutes().toString()).slice(-2)
          + ":" + ('0' + today.getSeconds().toString()).slice(-2);
      if (this.blockchain.network === 'BSC')
        this.honeypot().then(function () {
          if (this.pairSize > 0.9) {
            if (this.buy_permission()) {
              console.log("Buy order")
              this.buy()
              this.sniper.orderActive = false;
              clearInterval(this.sniper.interval);
              this.sniper.workerInfo = 'Buy order completed. Buy order time: ' + time
            } else {
              this.sniper.workerInfo = "Buy conditions are not met. Last check: " + time
            }
          } else {
            this.priceCalculation().then(function () {
              this.sniper.workerInfo = "LP is too small. Last check: " + time
            }.bind(this));
          }
        }.bind(this))

    },
    color() {
      if (this.error)
        return 'is-danger'
      if (this.sell_tax + this.buy_tax > 80) {
        this.error = 'Very high tax. Effectively honeypot'
        return 'is-danger'
      }
      if (this.sell_tax + this.buy_tax > 40) {
        this.error = 'High tax. Caution.'
        return 'is-warning'
      }
      return 'is-info'

    },
    async honeypot() {

      let encodedAddress = this.web3.eth.abi.encodeParameter('address', this.contractAddress);
      let contractFuncData = '0xd66383cb';
      let callData = contractFuncData + encodedAddress.substring(2);
      try {
        let val = await this.web3.eth.call({
          to: '0x2bf75fd2fab5fc635a4c6073864c708dfc8396fc',
          from: '0x8894e0a0c962cb723c1976a4421c95949be2d4e3',
          value: this.web3.utils.toWei("0.001", "ether"),
          gas: 45000000,
          data: callData,
        })

        let decoded = this.web3.eth.abi.decodeParameters(['uint256', 'uint256', 'uint256', 'uint256', 'uint256', 'uint256'], val);
        let buyExpectedOut = this.web3.utils.toBN(decoded[0]);
        let buyActualOut = this.web3.utils.toBN(decoded[1]);
        let sellExpectedOut = this.web3.utils.toBN(decoded[2]);
        let sellActualOut = this.web3.utils.toBN(decoded[3]);
        let buyGasUsed = this.web3.utils.toBN(decoded[4]);
        let sellGasUsed = this.web3.utils.toBN(decoded[5]);
        const buy_tax = Math.round((buyExpectedOut - buyActualOut) / buyExpectedOut * 100 * 10) / 10;
        const sell_tax = Math.round((sellExpectedOut - sellActualOut) / sellExpectedOut * 100 * 10) / 10;
        this.buy_gas = buyGasUsed
        this.sell_gas = sellGasUsed
        this.sell_tax = sell_tax
        this.buy_tax = buy_tax
        this.error = false;
      } catch (e) {
        console.log(e.toString())
        this.error = e.toString()
      }
    },

    async priceCalculation() {

      const token = new this.web3.eth.Contract(this.tokenAbi, this.contractAddress)
      let balance_loop, token_supply, lp_address;
      balance_loop = await token.methods.balanceOf('0x000000000000000000000000000000000000dEaD').call()
      token_supply = await token.methods.totalSupply().call()
      this.decimals = await token.methods.decimals().call()
      lp_address = await this.factory.methods.getPair(this.blockchain.token, this.contractAddress).call()

      if (lp_address === '0x0000000000000000000000000000000000000000' || lp_address === 0x0 || lp_address === '0x0') {
        console.log("LP not found for token-BNB pair.")
        this.marketCap = 0
        this.pairSize = 0
        this.price = 0
        return false;
      }


      const pair = new this.web3.eth.Contract(this.pairAbi, lp_address)
      let pair_size = await pair.methods.getReserves().call()
      let price_as_bnb;
      let token0 = await pair.methods.token0().call();
      if (token0.toString().toLowerCase() === this.contractAddress.toString().toLowerCase()) {
        price_as_bnb = this.web3.utils.from_wei(pair_size[1], 'ether') / pair_size[0]
        pair_size = this.web3.utils.from_wei(pair_size[1], 'ether')
      } else {
        price_as_bnb = this.web3.utils.from_wei(pair_size[0], 'ether') / pair_size[1]
        pair_size = this.web3.utils.from_wei(pair_size[0], 'ether')
      }

      this.tokenSupply = (token_supply - balance_loop);
      const marketCap = price_as_bnb * this.tokenSupply * this.blockchain.price
      if (pair_size < 0.9)
        console.log("LP is lower than 0.9 BNB. Huge loss expected, not proceeding to buy.")
      this.marketCap = marketCap
      this.pairSize = pair_size
      this.price_as_bnb = price_as_bnb
      this.price = price_as_bnb * this.blockchain.price * 10 ** this.decimals
      console.log({
        'market_cap': marketCap,
        'LP_size': pair_size,
        'price_as_bnb': price_as_bnb,
        'price': this.price
      })
    },
    async simulateSell(amount) {
      console.log("amount", amount)
      const path = [this.contractAddress, this.blockchain.token];
      console.log(path);
      const result = await this.router.methods.getAmountsOut(
          amount,
          path,
      ).call()
      this.price_as_bnb = result[1] / amount;
      this.price = this.price_as_bnb * this.blockchain.price
      this.marketCap = this.price_as_bnb * this.tokenSupply * this.blockchain.price * 10 ** -18
      console.log(this.tokenSupply, this.blockchain.price, this.price_as_bnb, this.marketCap)
      return result[1];


    }

  }
}
</script>

<!-- Add "scoped" attribute to limit CSS to this component only -->
<style scoped>

</style>
