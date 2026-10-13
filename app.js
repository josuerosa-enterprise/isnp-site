'use strict';
document.documentElement.classList.add('js');
const menuButton = document.querySelector('.menu-toggle');
const navigation = document.querySelector('#navigation');
function closeMenu() { menuButton.setAttribute('aria-expanded', 'false'); navigation.classList.remove('is-open'); }
menuButton.addEventListener('click', () => { const open = menuButton.getAttribute('aria-expanded') !== 'true'; menuButton.setAttribute('aria-expanded', String(open)); navigation.classList.toggle('is-open', open); });
navigation.querySelectorAll('a').forEach(link => link.addEventListener('click', closeMenu));
document.addEventListener('keydown', event => { if (event.key === 'Escape' && navigation.classList.contains('is-open')) { closeMenu(); menuButton.focus(); } });
window.matchMedia('(min-width: 901px)').addEventListener('change', event => { if (event.matches) closeMenu(); });
const proposalDialog = document.querySelector('#proposal-dialog');
const privacyDialog = document.querySelector('#privacy-dialog');
let dialogOpener = null;
function openDialog(dialog, opener) { dialogOpener = opener; closeMenu(); document.body.classList.add('modal-open'); dialog.showModal(); }
document.querySelectorAll('[data-open-proposal]').forEach(button => button.addEventListener('click', () => openDialog(proposalDialog, button)));
document.querySelector('#privacy-open').addEventListener('click', event => openDialog(privacyDialog, event.currentTarget));
document.querySelectorAll('dialog').forEach(dialog => {
  dialog.querySelectorAll('[data-close]').forEach(button => button.addEventListener('click', () => dialog.close()));
  dialog.addEventListener('close', () => {
    document.body.classList.remove('modal-open');
    if (!dialogOpener) return;
    // The mobile navigation closes when a proposal opens. Return focus to a visible control.
    const mobileNavigationOpener = navigation.contains(dialogOpener) && window.matchMedia('(max-width: 900px)').matches;
    (mobileNavigationOpener ? menuButton : dialogOpener).focus();
  });
  dialog.addEventListener('click', event => { if (event.target === dialog) { const box = dialog.getBoundingClientRect(); if (event.clientX < box.left || event.clientX > box.right || event.clientY < box.top || event.clientY > box.bottom) dialog.close(); } });
});
const form = document.querySelector('#proposal-form');
const result = document.querySelector('#proposal-result');
const output = document.querySelector('#proposal-output');
const status = document.querySelector('#proposal-status');
form.addEventListener('submit', event => {
  event.preventDefault();
  if (!form.reportValidity()) return;
  const data = new FormData(form);
  output.value = ['SOLICITAÇÃO DE PROPOSTA — GESTÃO MÉDICA', 'Ao Instituto de Saúde do Norte do Pará — ISNP', '', 'Hospital / instituição: ' + data.get('organization').trim(), 'Cidade / UF: ' + data.get('city').trim(), 'Contato e cargo: ' + data.get('contact').trim(), 'Serviço de interesse: ' + data.get('kind'), '', 'NECESSIDADE DO HOSPITAL', data.get('idea').trim(), '', 'Gostaria de conversar sobre uma proposta de gestão médica para nossa unidade.'].join('\n');
  document.querySelector('#whatsapp-proposal').href = 'https://wa.me/5594981081535?text=' + encodeURIComponent(output.value);
  document.querySelector('#email-proposal').href = 'mailto:institutodesaudedonortedopara@gmail.com?subject=' + encodeURIComponent('Solicitação de proposta de gestão médica — ISNP') + '&body=' + encodeURIComponent(output.value);
  form.hidden = true; result.hidden = false; status.textContent = ''; output.focus();
});
document.querySelector('#edit-proposal').addEventListener('click', () => { result.hidden = true; form.hidden = false; form.elements.organization.focus(); });
document.querySelector('#copy-proposal').addEventListener('click', async () => {
  try { await navigator.clipboard.writeText(output.value); status.textContent = 'Resumo copiado. Você já pode colá-lo na sua mensagem.'; }
  catch { output.focus(); output.select(); status.textContent = 'Selecione e copie o texto acima ou use a opção Baixar arquivo.'; }
});
document.querySelector('#download-proposal').addEventListener('click', () => {
  const blob = new Blob(['\uFEFF' + output.value], {type: 'text/plain;charset=utf-8'});
  const url = URL.createObjectURL(blob); const anchor = document.createElement('a'); anchor.href = url; anchor.download = 'solicitacao-gestao-medica-isnp.txt'; document.body.appendChild(anchor); anchor.click(); anchor.remove(); setTimeout(() => URL.revokeObjectURL(url), 1000); status.textContent = 'Resumo preparado para download. Para enviar ao instituto, escolha WhatsApp ou e-mail.';
});

const contactSection = document.querySelector('#conectar');
const contactDock = document.querySelector('.contact-dock');
if (contactSection && contactDock && 'IntersectionObserver' in window) {
  new IntersectionObserver(entries => {
    contactDock.classList.toggle('is-hidden', entries[0].isIntersecting);
  }, {threshold: 0}).observe(contactSection);
}
