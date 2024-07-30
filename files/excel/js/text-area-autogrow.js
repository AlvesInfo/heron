function debounce(callback, delay){
  let timer;
  return function(){
      let args = arguments;
      let context = this;
      clearTimeout(timer);
      timer = setTimeout(function(){
          callback.apply(context, args);
      }, delay)
  }
}

class Autogrow extends HTMLTextAreaElement {

  constructor () {
    super()
    this.onFocus = this.onFocus.bind(this)
    this.autogrow = this.autogrow.bind(this)
    this.onResize = debounce(this.onResize.bind(this), 300)
  }

  connectedCallback () {
    this.addEventListener('focus', this.onFocus)
  }

  disconnectedCallback () {
    window.removeEventListener('resize', this.onResize)
  }

  onFocus () {
    this.style.overflow = 'hidden'
    this.style.resize = 'none'
    this.style.boxSizing = 'border-box'
    this.autogrow()
    window.addEventListener('resize', this.onResize)
    this.addEventListener('input', this.autogrow)
    this.removeEventListener('focus', this.onFocus)
  }

  onResize () {
    this.autogrow()
  }

  autogrow () {
    this.style.height = 'auto'
    this.style.height = this.scrollHeight + 'px'
  }

}

customElements.define('textarea-autogrow', Autogrow, {extends: 'textarea'})

class AutogrowNow extends HTMLTextAreaElement {

  constructor () {
    super()
    this.autogrow = this.autogrow.bind(this)
    window.onload = this.autogrow()
  }

  autogrow () {
    this.style.height = 'auto'
    this.style.height = this.scrollHeight + 'px'
    this.style.overflow = 'hidden'
    this.style.resize = 'none'
    this.style.boxSizing = 'border-box'
  }

}

customElements.define('textarea-autogrow-now', AutogrowNow, {extends: 'textarea'})