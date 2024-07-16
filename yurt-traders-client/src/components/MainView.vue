<!--suppress ALL -->
<template>
  <div class="MainView">
    <b-navbar :type="darkMode ? 'is-dark' : 'is-light'" class="mb-5">
      <template #brand>
        <b-navbar-item>
          <img v-if="darkMode" src="/yurttraders.png">
          <img v-else src="/yurttraders-light.png">
        </b-navbar-item>
      </template>
      <template #start>
        <b-navbar-item v-if="ui.logged && blockchain.price">
          <strong>Blockchain</strong>&nbsp;<span class="has-text-info">{{ blockchain.network }}</span>&nbsp;|&nbsp;
          <strong>{{ blockchain.symbol }}</strong>&nbsp;<span
            class="has-text-info">{{ parseFloat(blockchain.price).toFixed(2) }}$</span>&nbsp;|&nbsp;
          <strong>Request Delay:</strong>&nbsp;<span class="has-text-info">{{ blockchain_delay }} ms</span> &nbsp;|&nbsp;
          <strong>Gas Price:</strong>&nbsp;<span class="has-text-info">{{ ui.gas_price }}</span><a
            v-on:click="calculateDelay()" class="mdi mdi-align-vertical-bottom mdi-refresh has-text-info mdi-24px"
            aria-hidden="true"></a>&nbsp;|&nbsp;
          <a v-if="wallets.length > 0" :class="telegramConnected ? 'has-text-link' : 'has-text-light'"
             v-on:click="telegramConnect()">{{
              telegramConnected ? 'Telegram Connected' : 'Telegram Disconnected'
            }}
          </a>&nbsp;|&nbsp;
          <a
              v-on:click="audio.paused ? audio.play(): audio.pause()">{{
              audio.paused ? 'Test Audio' : 'Stop Audio'
            }}
          </a>
        </b-navbar-item>
        <b-navbar-item v-else-if="ui.logged">
          <strong>Blockchain</strong>&nbsp;<span class="has-text-danger">Waiting server response...</span>
        </b-navbar-item>
        <b-navbar-item v-else>
          <strong>Blockchain</strong>&nbsp;<span class="has-text-warning">Login first...</span>
        </b-navbar-item>

      </template>

      <template #end>
        <b-navbar-dropdown v-if="ui.logged" :label="user.phone_number">
          <b-navbar-item v-on:click="logout()" href="#">
            Log out
          </b-navbar-item>
        </b-navbar-dropdown>
      </template>
    </b-navbar>
    <div class="container">
      <div class="columns">
        <div class="column is-8">
          <section>
            <b-tabs  v-model="activeTab">
              <b-tab-item v-if="!ui.logged" icon="account" label="Login | Register">
                <section class="box">
                  <b-field label="Phone number">
                    <b-input v-model="ui.phoneNumber"
                             placeholder="+49xxxxxxxx"
                             validation-message="Enter valid phone number including country code"
                             pattern="\+[0-9]{6,20}"
                    ></b-input>
                  </b-field>


                  <b-field label="Password">
                    <b-input type="password"
                             v-model="ui.password"
                             required
                             minlength="5"
                             password-reveal>
                    </b-input>
                  </b-field>
                  <b-button type="is-primary" v-on:click="login()" expanded>Login / Register</b-button>
                </section>
              </b-tab-item>
              <b-tab-item v-if="ui.logged" icon="wallet" label="Wallets">
                <b-button class="mb-5" expanded v-if="wallets.length > 0"
                          :type="telegramConnected ? 'is-danger' : 'is-info'" v-on:click="telegramConnect()">{{
                    telegramConnected ? 'Disconnect from Telegram' : 'Connect to Telegram'
                  }}
                </b-button>
                <mnemonic v-bind:ui="ui" v-bind:socket="socket"></mnemonic>
                <wallets v-if="blockchain.price" v-bind:wallets="wallets" v-bind:blockchain="blockchain"
                         v-bind:socket="socket"></wallets>
                <transfers v-bind:wallets="wallets" v-bind:blockchain="blockchain"
                           v-bind:socket="socket"></transfers>
              </b-tab-item>

              <b-tab-item icon="cog" v-if="ui.logged" label="Settings">
                <settings v-bind:wallets="wallets" v-bind:blockchain="blockchain"
                          v-bind:socket="socket" v-bind:user="user"></settings>
              </b-tab-item>
              <b-tab-item v-if="ui.logged" label="Token Interaction">
                <contract v-bind:activeContract="activeContract" :wallets="wallets" v-bind:blockchain="blockchain"
                          v-bind:socket="socket" v-bind:web3="web3">

                </contract>
              </b-tab-item>
              <b-tab-item v-if="ui.logged" icon="arrow-bottom-right" label="Presale">
                <presale
                    v-bind:wallets="wallets" v-bind:blockchain="blockchain"
                    v-bind:socket="socket" v-bind:web3="web3">
                </presale>
              </b-tab-item>
              <b-tab-item v-if="ui.logged" icon="send" label="Telegram">
                <telegram
                    v-bind:wallets="wallets" v-bind:blockchain="blockchain"
                    v-bind:socket="socket" v-bind:web3="web3">
                </telegram>
              </b-tab-item>
              <!--
              <b-tab-item v-if="ui.logged" icon="crosshairs-gps" label="Sniper">
                <sniper
                    v-bind:wallets="wallets" v-bind:blockchain="blockchain"
                    v-bind:socket="socket" v-bind:web3="web3">
                </sniper>
              </b-tab-item>-->
            </b-tabs>
          </section>
        </div>
        <div class="column is-4-desktop is-12-mobile">
          <section>
            <b-tabs>
              <b-tab-item label="Server Output">
                <b-button v-on:click="outputs = []" class="mb-5" type="is-secondary is-outlined" expanded>
                  Clear All Outputs
                </b-button>
                <!-- LEFT PANEL NOTIFICATIONS -->
                <transition-group name="slide-fade" tag="div">
                  <NotificationElement v-for="output in outputs.slice().reverse()" :key="output.id" v-bind:blockchain="blockchain"
                                       :output="output" v-bind:activeContract="activeContract" @setActiveContractAddress="setActiveContractAddress"
                      >
                  </NotificationElement>
                </transition-group>
              </b-tab-item>
            </b-tabs>
          </section>
        </div>
      </div>
    </div>
    <footer class="footer">
      <div class="content has-text-centered">
        <p>
          Yurt<strong style="color:rgb(150,200,240)">Traders</strong> by <a
            href="https://github.com/alakise">Alakise</a>💕 <br>All rights reserved.
        </p>
      </div>
    </footer>
  </div>
</template>

<script>
import {io} from "socket.io-client";
import Web3 from "web3";
import Wallets from "./wallets";
import Mnemonic from "./mnemonic";
import Transfers from "./transfers";
import Contract from "./contract";
import NotificationElement from "./templates/notification";
import Settings from "./settings";
import Presale from "./presale";
import soundFile from '@/assets/ME - Normandy Battle Alarm.mp3'
import message from '@/assets/incoming.mp3'
import telegramLogoutSound from '@/assets/ME - EDI - Logging you Out.mp3'
import telegramLoginSound from '@/assets/ME - Interface - Spectre Status Reco.mp3'
import Telegram from "./telegram";
// import Sniper from "./sniper";


export default {
  name: 'MainView',
  components: {Telegram, Settings, Contract, Transfers, Mnemonic, Wallets, Presale, NotificationElement},
  metaInfo() {
    let network = this.blockchain ? this.blockchain.network : '';
    network += ' | YurtTraders'
    return {
      titleTemplate: network
    }
  }
  ,
  data: function () {
    return {
      activeTab: undefined,
      socket: io(process.env.NODE_ENV === 'development' ? 'localhost:3059' : location.host),
      serverAddress: '',
      web3: null,
      outputs: [],
      outputCounter: 0,
      ui: {
        phoneNumber: localStorage.getItem('phoneNumber'),
        password: localStorage.getItem('password'),
        logged: false,
        mnemonics: '',
        gas_price: 'not calculated'

      },
      darkMode: true,
      activeContract: '',
      user: {},
      blockchain: {price: null, symbol: '', network: '', scanner: '', scanner_name: ''},
      blockchain_delay: 0,
      wallets: {},
      walletSearch: '',
      telegramConnected: false,
      audio: new Audio(soundFile),
      messageAudio: new Audio(message),
    }
  },

  watch: {
    web3() {
      this.calculateDelay();
    }
  },
  methods: {
    setActiveContractAddress(contractAddress){
        this.activeContract = contractAddress
        this.activeTab = 2;
    },
    calculateDelay() {
      const startTime = new Date();
      this.web3.eth.getGasPrice().then(function (data) {
        this.ui.gas_price = data * 10 ** -9
        this.blockchain_delay = new Date() - startTime;
      }.bind(this));
    },
    say(content) {
      let msg = new SpeechSynthesisUtterance();
      msg.text = content;
      window.speechSynthesis.speak(msg);
    },
    telegramConnect() {
      if (this.telegramConnected) {
        this.socket.emit('telegram_disconnect')
        this.telegramConnected = false
        let a = new Audio(telegramLogoutSound)
        a.play()
      } else {
        this.socket.emit('telegram_connect')
      }

    },
    send(event, args) {
      this.socket.emit(event, args);
    },
    createOutput(message = null, title = null, type = 'primary', message_content = false, decision = false) {
      let date = new Date();
      const minute = ('000' + date.getMinutes()).substr(-2);
      const hour = ('000' + date.getHours()).substr(-2);
      const day = ('000' + date.getDate()).substr(-2);
      const month = ('000' + (date.getMonth() + 1)).substr(-2);
      const seconds = ('000' + date.getSeconds()).substr(-2);
      date = [day, month].join('/') + ' ' + [hour, minute, seconds].join(":")
      if (title !== null)
        title = title + ' - ' + date
      else
        title = date
      this.outputs.push({
        id: this.outputCounter,
        type: type,
        message: message,
        title: title,
        message_content: message_content,
        decision: decision
      });
      this.outputCounter++;
    },
    setServer() {
      this.socket = io(this.serverAddress)
      localStorage.setItem('serverAddress', this.serverAddress)
    },
    login() {
      //phone_number, password
      console.log('Login attempt')
      if (this.ui.phoneNumber !== null && this.ui.password !== null) {
        this.send('login', {'phone_number': this.ui.phoneNumber, 'password': this.ui.password});
      }
    },
    logout() {
      console.log('Log out')
      this.send('log_out');
      localStorage.removeItem('phoneNumber');
      localStorage.removeItem('password');
      this.user = {};
      this.ui.logged = false;
    },
    save_mnemonics() {
      this.send('set_mnemonic', {'mnemonic': this.ui.mnemonics})
    },
    alert(title, message) {
      this.$buefy.dialog.alert({
        title: title,
        message: message,
      })
    },
    handleErrors() {
      this.$buefy.toast.open({
        duration: 5000,
        message: 'Socket error, local server offline',
        type: 'is-danger'
      })
    },
    walletByAddress(object, value) {
      if (Object.keys(object).find(key => object[key].address === value) !== undefined)
        return (parseInt(Object.keys(object).find(key => object[key].address === value)) + 1);
      else return "External"
    }
  },
  mounted: function () {
    /* DARK MODE START */
    // if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
    //   this.darkMode = true;
    // } else {
    //   this.darkMode = false;
    // }
    // window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', event => {
    //   this.darkMode = event.matches ? true : false;
    // });
    this.darkMode = true;
    /* DARK MODE END */
    this.audio.loop = true;
    console.log("Listening port on: ", process.env.NODE_ENV === 'development' ? 'localhost:3059' : location.host)
    console.log("Socket created:", this.socket);
    this.socket.on('connect_error', err => this.handleErrors(err))
    this.socket.on('connect_failed', err => this.handleErrors(err))
    this.socket.on('disconnect', err => this.handleErrors(err))
    //Events
    /*if (this.walletUpdater) {
      clearInterval(this.walletUpdater)
      this.walletUpdater = false;
    }
    this.walletUpdater = setInterval(function () {
      console.log('Wallets updated.');
      this.send('refresh_wallet', {login: false});
    }.bind(this), 60000)*/
    this.socket.on("connect", () => {
      this.createOutput('Connected to Socket', null, 'info')
      // Starters
      this.send('check_login', {login: false});
      if (this.telegramConnected) {
        this.socket.emit('telegram_disconnect')
        this.telegramConnected = false
        let a = new Audio(telegramLogoutSound)
        a.play()
      }

    });
    this.socket.on("test_response", (e) => {
      console.log(e)
    });
    this.socket.on("login_response", (e) => {
      if (e.success) {
        console.log(e);
        this.$buefy.toast.open({
          duration: 5000,
          message: 'Login successful',
          type: 'is-info'
        })
        localStorage.setItem('phoneNumber', this.ui.phoneNumber)
        localStorage.setItem('password', this.ui.password)
        this.ui.logged = true;
      } else {
        this.$buefy.toast.open({
          duration: 5000,
          message: e.error,
          type: 'is-danger'
        })
        localStorage.removeItem('phoneNumber')
        localStorage.removeItem('password')
        this.ui.logged = false
      }
    });
    this.socket.on("user_info_response", (e) => {
      console.log(e)
      if (e.success) {
        this.ui.logged = true;
        this.user = e.data;
        this.send('refresh_wallet', {login: false});
        if (!this.user.bot_token || this.user.bot_token.length < 15) {
          this.$buefy.toast.open({
            duration: 15000,
            message: 'Bot token is not set, functionality very limited.',
            type: 'is-danger'
          })
        }
      } else {
        this.login();
      }
    });
    this.socket.on("wallet_response", (e) => {
      console.log('Wallet response:', e)
      if (e.success) {
        this.blockchain = e.blockchain
        this.web3 = new Web3(e.blockchain.RPC)
        this.wallets = e.wallets

      } else {
        this.createOutput('Set your mnemonic', null, 'danger')
      }
    });
    this.socket.on("buy_response", (t) => {
      console.log(t);
      if (t.success)
        this.createOutput('Buy completed - TX on <a target="_blank" href=\''.concat(this.blockchain.scanner, "tx/").concat(t.tx, "'>").concat(this.blockchain.scanner_name, "</a><br>\nAmount: ").concat(t.amount, " ") + this.blockchain.symbol + '&nbsp;|&nbsp;' +
            '\n<a target="_blank" href=\''.concat(this.blockchain.scanner, "address/").concat(t.wallet, "'>Wallet ").concat(this.walletByAddress(this.wallets, t.wallet)), "Buy Success", "info");
      else
        this.createOutput(t.data, "Error on buy", "danger");
    })
    this.socket.on("approve_response", (t) => {
      console.log(t);
      if (t.success)
        this.createOutput('Approve completed - TX on <a target="_blank" href=\''.concat(this.blockchain.scanner, "tx/").concat(t.tx, "'>").concat(this.blockchain.scanner_name, "</a>"), "Token Approved", "info")
      else
        this.createOutput(t.data, "Error on approval", "warning")
    })
    this.socket.on("transfer_response", (t) => {
      console.log(t);
      if (t.success)
        this.createOutput('Transfer completed -\nTX on <a target="_blank" href=\''.concat(this.blockchain.scanner, "tx/").concat(t.tx, "'>").concat(this.blockchain.scanner_name, '</a><br>\n' +
            'From <a target="_blank" href=\'').concat(this.blockchain.scanner, "address/").concat(t.from, "'>Wallet ").concat(this.walletByAddress(this.wallets, t.from), '</a>&nbsp;to&nbsp;\n<a target="_blank" href=\'').concat(this.blockchain.scanner, "address/").concat(t.to, "'>Wallet ").concat(this.walletByAddress(this.wallets, t.to), "</a>"), "Balance Transferred", "info")
      else
        this.createOutput(t.data, "Error on transfer", "warning");
    })
    this.socket.on("sell_response", (t) => {
      console.log(t);
      if (t.success)
        this.createOutput('Sell completed -\nTX on <a target="_blank" href=\''.concat(this.blockchain.scanner, "tx/").concat(t.tx, "'>").concat(this.blockchain.scanner_name, "</a>"), "Sell Success", "info")
      else
        this.createOutput(t.data, "Error on sell", "warning");
    })
    this.socket.on("telegram_connect_response", (t) => {
      console.log("Telegram Connected", t);
      this.telegramConnected = true;
      if (t.success) {
        this.createOutput("Telegram account connected: <b>@".concat(t.me.username, "</b>"), "Telegram Connected", "info");
        let a = new Audio(telegramLoginSound)
        a.play()
      } else
        this.createOutput(t.data, "Error on telegram login", "warning");
    })
    this.socket.on("message_response", (t) => {
      console.log("New Message", t);
      this.createOutput("Chat: <b>" + t.title + "</b><br>" + t.data, "✉️ New Message", "primary", t.message_content, t.decision)
    })
    this.socket.on("nuke_response", () => {
      console.log('ui_sound_test')
      this.audio.play()
    })
    this.socket.on("buy_alarm_stop", () => {
      this.audio.pause();
      this.audio.currentTime = 0
    })
    this.socket.on("important_alarm_response", () => {
      console.log("Important Message")
      this.messageAudio.play()
    })
    this.socket.on("sound_test", () => {
      console.log('sound_test')
      this.say("Your trade bot is online and scanning the telegram. Connected network is: " + this.blockchain.network)
    })


  }
}
</script>

<!-- Add "scoped" attribute to limit CSS to this component only -->
<style scoped>
.panel-block:not(:last-child), .panel-tabs:not(:last-child) {
  border-bottom: 1px solid darkslategrey;
}

/* Enter and leave animations can use different */
/* durations and timing functions.              */
.slide-fade-enter-active {
  transition: all .5s ease-in-out;
}

.slide-fade-leave-active {
  transition: all .5s ease-in-out;
}

.slide-fade-enter, .slide-fade-leave-to
  /* .slide-fade-leave-active below version 2.1.8 */
{
  transform: translateY(-60px);
  opacity: 0;
}

</style>
<style>
.message {
  transition: all .5s ease-in-out;
}

.tabs ul {
  border: 2px solid hsl(182, 92%, 15%) !important;
  background-color: hsla(180, 100%, 5%, 0.7) !important;
  border-radius: 5px;
  margin: 0 10px 0 10px;
  padding: 5px;
}

.tabs li a {
  color: #d2d2d2;
  border-bottom: none;
}

.tabs li.is-active a {
  color: #70c8ff !important;
}

.tabs li {

}

.tabs a:hover {
  border-bottom-color: #ffffff !important;
  color: #ffffff !important;
}

html {
  background-color: white;
  background: linear-gradient(90deg, rgb(200, 200, 200) 0%, rgb(225, 225, 225) 50%, rgb(200, 200, 200) 100%);

}

body {
  background-image: url('~@/assets/hexagon-light-mode.png');
  background-position: top left;
  background-repeat: repeat;
  background-size: 350px;
  min-height: 100vh;
  transition: ease 0.3s;
}


nav.navbar.is-light {
  background: rgba(255, 255, 255, 0.5);
  background: linear-gradient(0deg, rgba(200, 200, 200, 0) 0%, rgba(255, 255, 255, 0.7) 100%);
}

.navbar.is-light .navbar-brand > a.navbar-item:hover {
  background-color: transparent !important;
}


html {
  background-color: black;
  background: linear-gradient(90deg, rgb(10, 5, 13) 0%, rgb(10, 31, 51) 50%, rgb(3, 13, 7) 100%);

}

nav.navbar.is-dark {
  background: rgba(0, 0, 0, 0.5);
  background: linear-gradient(0deg, rgba(0, 0, 0, 0) 0%, rgba(0, 0, 0, 1) 100%);
}

body {
  background-image: url('~@/assets/hexagon.png');
  background-position: top left;
  background-repeat: repeat;
  background-size: 350px;
  min-height: 100vh;
  transition: ease 0.3s;
}


.card {
  background-color: hsla(180, 100%, 5%, 0.7) !important;
  border: 2px solid hsl(182, 92%, 15%) !important;
}

footer.footer {
  background: transparent !important;
  background-color: transparent !important;
}
</style>
